from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage
import cv2
from src.utils.drawing_utils import draw_landmarks
from src.config import Config
import numpy as np
from utils.logger import AppLogger

class VideoProcessor(QObject):
    update_frame_signal = pyqtSignal(QImage)
    siz_status_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer()
        self.logger = AppLogger.get_logger()
        self.timer.timeout.connect(self._process_frame)
        self._setup_parameters()
        self._init_camera()

    def _setup_parameters(self):
        self.show_landmarks = True
        self.active_model_type = None
        self.model_loaded = False
        self.siz_detected = False
        self.processing_active = False
        self.detectors_ready = False

    def _init_camera(self):
        self.cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        if not self.cap.isOpened():
            self.logger.error("Не удалось открыть камеру")
            raise RuntimeError("Не удалось открыть камеру")

    def set_detectors(self, yolo, face, pose, siz):
        self.yolo = yolo
        self.face = face
        self.pose = pose
        self.siz = siz
        self.detectors_ready = True

    @pyqtSlot(str, dict)
    def load_model(self, model_type, model_info):
        """Загрузка модели в детектор"""
        if not self.detectors_ready:
            return False
            
        try:
            if self.yolo.load_model(model_type, model_info):
                self.active_model_type = model_type
                self.model_loaded = True
                self.logger.info(f"Модель {model_type} успешно загружена в детектор")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели в детектор: {str(e)}")
            return False

    @pyqtSlot()
    def start_processing(self):
        if not self.active_model_type:
            return
            
        if not self.timer.isActive():
            # Сброс предыдущего состояния
            self.siz_detected = False  
            self.timer.start(30)

    @pyqtSlot()
    def stop_processing(self):
        """Полная остановка обработки"""
        if self.timer.isActive():
            self.timer.stop()
            self.logger.info("Обработка видео остановлена")

    @pyqtSlot(bool)
    def toggle_landmarks(self, state):
        """Метод для переключения отображения ключевых точек"""
        self.show_landmarks = state

    def _process_frame(self):
        """Основной цикл обработки кадра"""
        if not self.active_model_type:
            return
            
        ret, frame = self.cap.read()
        if not ret:
            return
            
        try:
            # Обработка кадра и детекция
            processed_frame = self._process_detections(frame)
            self._emit_frame(processed_frame)
            
        except Exception as e:
            self.logger.error(f"Ошибка обработки: {str(e)}")

    def _process_detections(self, frame):
        frame = frame.copy()
        
        # Детекция объектов
        frame, boxes = self.yolo.detect(frame, self.active_model_type)
        
        # Инициализация результатов детекции
        pose_results = None
        face_results = None
        
        # Определяем необходимость детекции ключевых точек
        need_face = (boxes and self.active_model_type == "glasses") or self.show_landmarks
        need_pose = (boxes and self.active_model_type == "ppe") or self.show_landmarks
        
        if need_face:
            face_results = self.face.detect(frame)
        if need_pose:
            pose_results = self.pose.detect(frame)

        # Проверка СИЗ (только если есть боксы)
        if boxes:
            siz_statuses = self._check_compliance(boxes, pose_results, face_results, frame.shape)
            frame = self._draw_detections(frame, boxes, siz_statuses)
            self._update_siz_status(siz_statuses)

        # Отрисовка ключевых точек (только если включено)
        if self.show_landmarks and (pose_results or face_results):
            draw_landmarks(frame, pose_results, face_results)
        
        return frame

    def _check_compliance(self, boxes, pose_results, face_results, frame_shape):
        if not boxes:
            return []
            
        try:
            if self.active_model_type == "glasses":
                if face_results is None:
                    face_results = self.face.detect(np.zeros((10,10,3), dtype=np.uint8))  # Пустой фрейм для инициализации
                return self.siz.check_glasses(boxes, face_results, frame_shape)
                
            elif self.active_model_type == "ppe":
                if pose_results is None:
                    pose_results = self.pose.detect(np.zeros((10,10,3), dtype=np.uint8))
                return self.siz.check_ppe(boxes, pose_results, frame_shape)
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки СИЗ: {str(e)}")
            return [False] * len(boxes.xyxy)
            
        return []

    def _draw_detections(self, frame, boxes, statuses):
        for box, status in zip(boxes.xyxy, statuses):
            x1, y1, x2, y2 = map(int, box.cpu().numpy())
            color = (0, 255, 0) if status else (0, 0, 255)
            
            # Рисуем bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Подпись с типом СИЗ и статусом
            label = f"{'OK' if status else 'FAIL'}"
            cv2.putText(frame, label, (x1, y1-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame

    def _update_siz_status(self, statuses):
        if not statuses:
            new_status = False
        else:
            new_status = all(statuses) if self.active_model_type == "ppe" else any(statuses)
        
        if new_status != self.siz_detected:
            self.siz_detected = new_status
            self.siz_status_changed.emit(self.siz_detected)

    def _emit_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        q_img = QImage(rgb_frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.update_frame_signal.emit(q_img)

    def cleanup(self):
        """Полная очистка ресурсов"""
        self.stop_processing()
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()