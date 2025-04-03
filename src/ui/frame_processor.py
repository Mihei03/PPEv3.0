import cv2
import numpy as np
from PyQt6.QtGui import QImage
from utils.logger import AppLogger
from .detection_drawer import DetectionDrawer

class FrameProcessor:
    def __init__(self):
        self.logger = AppLogger.get_logger()
        self.detectors = {}
        self.drawer = DetectionDrawer()
        self.show_landmarks = False
        self.last_face_results = None
        self.last_pose_results = None

    def set_detectors(self, yolo, face, pose, siz):
        self.detectors = {
            'yolo': yolo,
            'face': face,
            'pose': pose,
            'siz': siz
        }
        self.drawer.set_detectors(yolo, siz)

    def load_model(self, model_type, model_info):
        if not self.detectors.get('yolo'):
            return False
            
        try:
            if self.detectors['yolo'].load_model(model_type, model_info):
                if 'class_names' in model_info:
                    self.detectors['yolo'].class_names[model_type] = model_info['class_names']
                self.logger.info(f"Модель {model_type} загружена успешно")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {str(e)}")
            return False

    def process(self, frame, model_type=None):
        frame = frame.copy()
        status = None
        
        try:
            # Детекция лиц и позы
            face_results = self.detectors['face'].detect(frame) if 'face' in self.detectors else None
            pose_results = self.detectors['pose'].detect(frame) if 'pose' in self.detectors else None

            # Логирование для диагностики
            self.logger.debug(f"Face results type: {type(face_results)}")
            self.logger.debug(f"Pose results type: {type(pose_results)}")

            # YOLO детекция
            boxes = None
            if model_type and 'yolo' in self.detectors:
                _, boxes = self.detectors['yolo'].detect(frame, model_type)

            # Обработка результатов YOLO
            if boxes is not None and hasattr(boxes, 'xyxy') and len(boxes.xyxy) > 0:
                status = self._check_compliance(boxes, pose_results, face_results, frame.shape, model_type)
                frame = self.drawer.draw_detections(frame, boxes, status, model_type)
            else:
                status = "nothing"

            # Отрисовка ключевых точек
            if self.show_landmarks:
                frame = self.drawer.draw_landmarks(frame, pose_results, face_results)
                self.logger.debug("Landmarks drawing attempted")

        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")
            status = False
            
        return frame, status

    def draw_landmarks(self, frame):
        """Отдельный метод для отрисовки ключевых точек"""
        if self.last_pose_results is not None or self.last_face_results is not None:
            try:
                frame = self.drawer.draw_landmarks(frame, self.last_pose_results, self.last_face_results)
                self.logger.debug("Landmarks were drawn successfully")
            except Exception as e:
                self.logger.error(f"Error drawing landmarks: {str(e)}")
        else:
            self.logger.debug("No landmarks data to draw")
        return frame

    def _check_compliance(self, boxes, pose_results, face_results, frame_shape, model_type):
        if 'siz' not in self.detectors:
            return False
            
        try:
            class_names = self.detectors['yolo'].class_names.get(model_type, [])
            return self.detectors['siz'].check_items(
                boxes, pose_results, face_results, frame_shape, class_names
            )
        except Exception as e:
            self.logger.error(f"Compliance check error: {str(e)}")
            return [False] * len(boxes.xyxy)

    def convert_to_qimage(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

    def toggle_landmarks(self, state):
        self.show_landmarks = state
        self.logger.info(f"Landmarks visibility: {'ON' if state else 'OFF'}")