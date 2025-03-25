from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage
import cv2
from src.utils.drawing_utils import draw_landmarks
from src.config import Config
import numpy as np
from utils.logger import AppLogger

class VideoProcessor(QObject):
    update_frame_signal = pyqtSignal(QImage)
    siz_status_changed = pyqtSignal(object)
    
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
            self.logger.info("Обработка видео начато")
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
        
        # 1. Инициализация результатов с защитой от None
        pose_results = None
        face_results = None
        boxes = None
        siz_statuses = []

        try:
            # 2. Всегда делаем детекцию ключевых точек (но защищаемся от ошибок)
            if self.show_landmarks or self.active_model_type:
                try:
                    face_results = self.face.detect(frame) if hasattr(self.face, 'detect') else None
                    pose_results = self.pose.detect(frame) if hasattr(self.pose, 'detect') else None
                except Exception as e:
                    self.logger.warning(f"Ошибка детекции ключевых точек: {str(e)}")

            # 3. Детекция объектов YOLO (с защитой от ошибок)
            if self.active_model_type:
                try:
                    _, boxes = self.yolo.detect(frame, self.active_model_type)
                except Exception as e:
                    self.logger.error(f"Ошибка детекции YOLO: {str(e)}")
                    boxes = None

            # 4. Проверка СИЗ только если есть что проверять
            if boxes and len(boxes.xyxy) > 0:
                try:
                    siz_statuses = self._check_compliance(boxes, pose_results, face_results, frame.shape)
                    if not siz_statuses:  # Если вернулся пустой список
                        siz_statuses = [False] * len(boxes.xyxy)
                    
                    # Отрисовка с цветами по статусу
                    frame = self.yolo._draw_custom_boxes(
                        frame, 
                        boxes.xyxy, 
                        boxes.conf.cpu().numpy(), 
                        boxes.cls.cpu().numpy().astype(int), 
                        siz_statuses, 
                        self.active_model_type
                    )
                    self._update_siz_status(siz_statuses)
                except Exception as e:
                    self.logger.error(f"Ошибка проверки СИЗ: {str(e)}")
                    # Рисуем все боксы красными при ошибке
                    siz_statuses = [False] * len(boxes.xyxy)
                    frame = self.yolo._draw_custom_boxes(
                        frame, 
                        boxes.xyxy, 
                        boxes.conf.cpu().numpy(), 
                        boxes.cls.cpu().numpy().astype(int), 
                        siz_statuses, 
                        self.active_model_type
                    )

            # 5. Отрисовка ключевых точек (если включено и есть результаты)
            if self.show_landmarks:
                try:
                    if pose_results or face_results:
                        draw_landmarks(frame, pose_results, face_results)
                except Exception as e:
                    self.logger.error(f"Ошибка отрисовки ключевых точек: {str(e)}")

        except Exception as e:
            self.logger.error(f"Критическая ошибка обработки кадра: {str(e)}")

        return frame

    def _check_compliance(self, boxes, pose_results, face_results, frame_shape):
        """Усовершенствованная проверка соответствия с полной защитой от None"""
        try:
            # 1. Проверка входных данных
            if boxes is None or not hasattr(boxes, 'xyxy') or len(boxes.xyxy) == 0:
                return []
                
            # 2. Подготовка списка статусов
            num_boxes = len(boxes.xyxy)
            default_status = [False] * num_boxes
            
            # 3. Проверка для разных типов моделей
            if self.active_model_type == "glasses":
                if face_results is None or not hasattr(face_results, 'multi_face_landmarks'):
                    return default_status
                try:
                    return self.siz.check_glasses(boxes, face_results, frame_shape) or default_status
                except:
                    return default_status
                    
            elif self.active_model_type == "ppe":
                if pose_results is None or not hasattr(pose_results, 'pose_landmarks'):
                    return default_status
                try:
                    return self.siz.check_ppe(boxes, pose_results, frame_shape) or default_status
                except:
                    return default_status
                    
            return default_status
            
        except Exception as e:
            self.logger.error(f"Ошибка в _check_compliance: {str(e)}")
            return [False] * len(boxes.xyxy) if boxes and hasattr(boxes, 'xyxy') else []

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
        """Определение общего статуса на основе списка статусов"""
        if statuses == "nothing":
            new_status = "nothing"
        elif not statuses:
            new_status = False
        else:
            new_status = all(statuses) if isinstance(statuses, list) else False
        
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