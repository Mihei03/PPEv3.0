from collections import deque
import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal, QThread
import cv2
import numpy as np
from core.utils.input_validator import InputType
from core.utils.logger import AppLogger
from .input_handler import InputHandler
from src.core.processing.frame_processor import FrameProcessor
from PyQt6.QtGui import QImage

class VideoProcessor(QObject):
    update_frame = pyqtSignal(QImage)
    siz_status_changed = pyqtSignal(object)
    input_error = pyqtSignal(str)
    processing_stopped = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = AppLogger.get_logger()
        self.timer = QTimer()
        self.timer.timeout.connect(self._process_frame)
        self.frame_times = deque(maxlen=30)
        self.last_frame_time = time.time()
        self.input_handler = InputHandler()
        self.frame_processor = FrameProcessor()
        
        self.target_fps = 30
        self.frame_skip_counter = 0
        self.video_start_time = 0
        self.last_video_pts = -1
        self.frame_drop_threshold = 2
        self.consecutive_drops = 0
        self._alive = True

        self._setup_initial_state()

    def _setup_initial_state(self):
        self.processing_active = False
        self.model_loaded = False
        self.active_model_type = None
        self._alive = True

    def set_detectors(self, yolo, pose, siz):
        self.frame_processor.set_detectors(yolo, pose, siz)

    def set_video_source(self, source, selected_source_type):
        self.stop_processing()
        success, error_msg = self.input_handler.setup_source(source, selected_source_type)
        
        if success and self.input_handler.is_file_source():
            fps = self.input_handler.cap.get(cv2.CAP_PROP_FPS)
            self.frame_interval = 1000 / fps if fps > 0 else 33
        return success, error_msg

    def load_model(self, model_type, model_info):
        success = self.frame_processor.load_model(model_type, model_info)
        if success:
            self.active_model_type = model_type
            self.model_loaded = True
        return success

    def start_processing(self):
        if not self.input_handler.is_ready():
            self.input_error.emit("Источник не инициализирован")
            self.logger.error("Попытка запуска с неинициализированным источником")
            return
            
        if not self.timer.isActive():
            self.processing_active = True
            self.video_start_time = time.time()
            self.last_video_pts = -1
            
            if self.input_handler.is_file_source():
                # Дополнительная проверка для файлового источника
                if not self.input_handler.cap or not self.input_handler.cap.isOpened():
                    self.input_error.emit("Не удалось открыть видеофайл")
                    self.logger.error("Видеофайл не открыт")
                    return
                self.timer.start(0)
            else:
                self.timer.start(33)

    def stop_processing(self):
        if not self._alive:
            return
            
        self.processing_active = False
        if self.timer.isActive():
            self.timer.stop()
        
        self.input_handler.release()
        
        if self._alive:
            self.processing_stopped.emit()
        self.logger.info("Обработка видео остановлена")

    def cleanup(self):
        self._alive = False
        self.stop_processing()

    def _process_frame(self):
        if not self.processing_active or not self._alive:
            return
            
        try:
            # Получаем кадр с явной проверкой на None
            ret, frame = self.input_handler.read_frame()
            if frame is None:
                if self.input_handler.is_file_source():
                    self.stop_processing()
                return

            # Для файлов - синхронизация времени
            if self.input_handler.is_file_source():
                current_pts = self.input_handler.cap.get(cv2.CAP_PROP_POS_MSEC)
                real_time = (time.time() - self.video_start_time) * 1000
                
                if current_pts < real_time:
                    skip_frames = int((real_time - current_pts) / self.frame_interval)
                    skip_frames = min(skip_frames, self.frame_drop_threshold)
                    
                    for _ in range(skip_frames):
                        if self.input_handler.read_frame()[1] is None:
                            break
                    self.consecutive_drops += skip_frames
                else:
                    self.consecutive_drops = 0

            # Обработка кадра, если не превышен лимит пропусков
            if self.consecutive_drops < self.frame_drop_threshold:
                processed_frame, status = self.frame_processor.process(frame, self.active_model_type)
                
                if processed_frame is not None:
                    self._emit_frame(processed_frame)
                if status is not None:
                    self.siz_status_changed.emit(status)
            else:
                self.consecutive_drops -= 1
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки кадра: {str(e)}", exc_info=True)

    def _emit_frame(self, frame):
        if self._alive:
            self.update_frame.emit(self.frame_processor.convert_to_qimage(frame))

    def toggle_landmarks(self, state):
        self.frame_processor.toggle_landmarks(state)