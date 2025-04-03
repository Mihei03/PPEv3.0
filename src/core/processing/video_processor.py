from collections import deque
import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
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
        
        self._setup_initial_state()

    def _setup_initial_state(self):
        self.processing_active = False
        self.model_loaded = False
        self.active_model_type = None

    def set_detectors(self, yolo, face, pose, siz):
        self.frame_processor.set_detectors(yolo, face, pose, siz)

    def set_video_source(self, source, selected_source_type):
        self.stop_processing()
        success, error_msg = self.input_handler.setup_source(source, selected_source_type)
        
        if error_msg:
            self.input_error.emit(error_msg)
            return False
        return success

    def load_model(self, model_type, model_info):
        success = self.frame_processor.load_model(model_type, model_info)
        if success:
            self.active_model_type = model_type
            self.model_loaded = True
        return success

    def start_processing(self):
        if not self.input_handler.is_ready():
            self.input_error.emit("Источник не инициализирован")
            return
            
        if not self.timer.isActive():
            self.processing_active = True
            self.timer.start(60)
            self.logger.info("Обработка видео запущена")

    def stop_processing(self):
        if self.timer.isActive():
            self.timer.stop()
        self.processing_active = False
        self.input_handler.release()
        self.processing_stopped.emit()  # Отправляем сигнал
        self.logger.info("Обработка видео остановлена, ресурсы освобождены")

    def _process_frame(self):
        if not self.processing_active:
            return
            
        # Пропускаем кадры если обработка отстает
        if len(self.frame_times) > 0 and time.time() - self.last_frame_time < 0.03:
            return
            
        try:
            start_time = time.time()
            frame = self.input_handler.get_frame()
            
            if frame is None:
                if self.input_handler.is_file_source():
                    self.stop_processing()
                return
                
            # Обработка кадра
            processed_frame, status = self.frame_processor.process(frame, self.active_model_type)
            
            # Контроль FPS
            self.frame_times.append(time.time() - start_time)
            self.last_frame_time = time.time()
            
            # Если задержка больше порога - пропускаем следующий кадр
            if len(self.frame_times) > 10 and sum(self.frame_times)/len(self.frame_times) > 0.05:
                self.logger.warning(f"Высокая задержка: {sum(self.frame_times)/len(self.frame_times):.3f} сек/кадр")
                
            # Отправка кадра
            if processed_frame is not None:
                self._emit_frame(processed_frame)
            if status is not None:
                self.siz_status_changed.emit(status)
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки кадра: {str(e)}")

    def _emit_frame(self, frame):
        self.update_frame.emit(self.frame_processor.convert_to_qimage(frame))

    def toggle_landmarks(self, state):
        self.logger.debug(f"Setting landmarks visibility to: {state}")
        self.frame_processor.toggle_landmarks(state)