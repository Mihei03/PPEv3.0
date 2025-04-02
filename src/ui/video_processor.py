from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage
import cv2
from src.utils.drawing_utils import draw_landmarks
from utils.logger import AppLogger
from src.detection.input_validator import InputValidator, InputType

class VideoProcessor(QObject):
    update_frame = pyqtSignal(QImage)
    siz_status_changed = pyqtSignal(object)
    input_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.logger = AppLogger.get_logger()
        self.timer.timeout.connect(self._process_frame)
        self._setup_initial_state()

    def _setup_initial_state(self):
        self.cap = None
        self.current_image = None
        self.current_input_type = None
        self.processing_active = False
        self.show_landmarks = True
        self.active_model_type = None
        self.model_loaded = False
        self.detectors = {}

    def set_detectors(self, yolo, face, pose, siz):
        self.detectors = {
            'yolo': yolo,
            'face': face,
            'pose': pose,
            'siz': siz
        }

    @pyqtSlot(str, int)
    def set_video_source(self, source, selected_source_type):
        self.stop_processing()
    
        input_type, normalized_source, error_msg = InputValidator.validate_input(
            source, selected_source_type
        )
        
        if error_msg:
            self.input_error.emit(error_msg)
            return False

        if self.cap:
            self.cap.release()
        
        try:
            if input_type == InputType.CAMERA:
                self.cap = cv2.VideoCapture(int(normalized_source))
            elif input_type == InputType.RTSP:
                self.cap = cv2.VideoCapture(normalized_source, cv2.CAP_FFMPEG)
            elif input_type == InputType.FILE:
                self.cap = cv2.VideoCapture(normalized_source)
            
            if self.cap and self.cap.isOpened():
                self.current_input_type = input_type
                return True
            return False
            
        except Exception as e:
            self.input_error.emit(f"Ошибка: {str(e)}")
            return False

    def _reset_validation(self):
        """Сбрасывает состояние валидации всех полей"""
        for input_field in [self.ui.camera_input, self.ui.video_input, self.ui.rtsp_input]:
            input_field.setProperty("valid", "unknown")
        self._update_input_styles()

    def _update_input_styles(self):
        """Обновляет стили всех полей ввода"""
        for input_field in [self.ui.camera_input, self.ui.video_input, self.ui.rtsp_input]:
            input_field.style().unpolish(input_field)
            input_field.style().polish(input_field)
            input_field.update()
            
    @pyqtSlot(str, dict)
    def load_model(self, model_type, model_info):
        if not self.detectors:
            return False
            
        try:
            if self.detectors['yolo'].load_model(model_type, model_info):
                self.active_model_type = model_type
                if 'class_names' in model_info:
                    self.detectors['yolo'].class_names[model_type] = model_info['class_names']
                self.model_loaded = True
                self.logger.info(f"Модель {model_type} загружена успешно")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {str(e)}")
            return False

    @pyqtSlot()
    def start_processing(self):
        if not self.cap and not self.current_image:
            self.input_error.emit("Источник не инициализирован")
            return
            
        if not self.timer.isActive():
            self.processing_active = True
            self.timer.start(60)
            self.logger.info("Обработка видео запущена")

    @pyqtSlot()
    def stop_processing(self):
        if self.timer.isActive():
            self.timer.stop()
        self.processing_active = False
        self.logger.info("Обработка видео остановлена")

    def _process_frame(self):
        try:
            if self.current_input_type == InputType.IMAGE:
                if self.current_image is not None:
                    processed = self._process_detections(self.current_image.copy())
                    self._emit_frame(processed)
                return
                
            if not self.cap or not self.cap.isOpened():
                self.logger.warning("Источник не готов")
                return
                
            ret, frame = self.cap.read()
            if ret:
                processed = self._process_detections(frame)
                self._emit_frame(processed)
            elif self.current_input_type == InputType.FILE:
                self.stop_processing()
                
        except Exception as e:
            self.logger.error(f"Ошибка обработки: {str(e)}")
            self.stop_processing()

    def _process_detections(self, frame):
        frame = frame.copy()
        
        try:
            face_results = self.detectors['face'].detect(frame) if 'face' in self.detectors else None
            pose_results = self.detectors['pose'].detect(frame) if 'pose' in self.detectors else None

            boxes = None
            if self.active_model_type and 'yolo' in self.detectors:
                try:
                    _, boxes = self.detectors['yolo'].detect(frame, self.active_model_type)
                except Exception as e:
                    self.logger.error(f"YOLO detection error: {str(e)}")
                    boxes = None

            if boxes is not None and hasattr(boxes, 'xyxy') and len(boxes.xyxy) > 0:
                class_names = self.detectors['yolo'].class_names.get(self.active_model_type, [])
                
                statuses = []
                try:
                    statuses = self.detectors['siz'].check_items(boxes, pose_results, face_results, frame.shape, class_names)
                except Exception as e:
                    self.logger.error(f"Compliance check error: {str(e)}")
                    statuses = [False] * len(boxes.xyxy)
                
                self.siz_status_changed.emit(statuses if statuses else False)
                frame = self._draw_detections_with_labels(frame, boxes, statuses, class_names)
            else:
                self.siz_status_changed.emit("nothing")

            if self.show_landmarks and (pose_results or face_results):
                try:
                    draw_landmarks(frame, pose_results, face_results)
                except Exception as e:
                    self.logger.error(f"Landmark drawing error: {str(e)}")

        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")
            self.siz_status_changed.emit(False)
        
        return frame

    def _draw_detections_with_labels(self, frame, boxes, statuses, class_names):
        try:
            if boxes is None or not hasattr(boxes, 'xyxy'):
                return frame
                
            for i, box in enumerate(boxes.xyxy):
                try:
                    x1, y1, x2, y2 = map(int, box.cpu().numpy())
                    status = statuses[i] if i < len(statuses) else False
                    
                    cls_id = int(boxes.cls[i].cpu().numpy()) if i < len(boxes.cls) else 0
                    conf = float(boxes.conf[i].cpu().numpy()) if i < len(boxes.conf) else 0.0
                    class_name = str(class_names[cls_id]) if (class_names and cls_id < len(class_names)) else f"Class {cls_id}"
                    
                    color = (0, 255, 0) if status else (0, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    label = f"{class_name} {conf:.2f}"
                    cv2.putText(frame, label, (x1, max(y1-10, 20)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                except Exception as e:
                    self.logger.warning(f"Error drawing box {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Drawing error: {str(e)}")
        
        return frame

    def _emit_frame(self, frame):
        try:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.update_frame.emit(qt_image)
        except Exception as e:
            self.logger.error(f"Ошибка преобразования кадра: {str(e)}")

    @pyqtSlot(bool)
    def toggle_landmarks(self, state):
        self.show_landmarks = state
        self.logger.info(f"Отображение ключевых точек: {'включено' if state else 'выключено'}")