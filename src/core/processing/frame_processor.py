import cv2
import numpy as np
from PyQt6.QtGui import QImage
from core.utils.drawing_utils import draw_landmarks
from core.utils.logger import AppLogger
from src.ui.builders.detection_drawer import DetectionDrawer

class FrameProcessor:
    def __init__(self):
        self.logger = AppLogger.get_logger()
        self.detectors = {}
        self.drawer = DetectionDrawer()
        self.show_landmarks = False
        self.last_face_results = None
        self.last_pose_results = None

    def set_detectors(self, yolo, pose, siz):
        self.detectors = {
            'yolo': yolo,
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
            # Инициализация результатов
            pose_results = None
            
            if self.detectors.get('pose') is not None:
                pose_results = self.detectors['pose'].detect(frame)
                if pose_results is not None and hasattr(pose_results, 'pose_landmarks'):
                    pose_results = pose_results if pose_results.pose_landmarks else None

            # YOLO детекция
            boxes = None
            if model_type and self.detectors.get('yolo') is not None:
                _, boxes = self.detectors['yolo'].detect(frame, model_type)

            # Безопасная проверка boxes
            boxes_valid = boxes is not None and hasattr(boxes, 'xyxy') and len(boxes.xyxy) > 0
            
            if boxes_valid:
                status = self._check_compliance(boxes, pose_results, frame.shape, model_type)
                if hasattr(status, 'any'):  # Проверяем, является ли status numpy array
                    status = status.tolist()
                
                # Проверяем, что статус содержит кортеж (statuses, people_count, detected_siz)
                if isinstance(status, tuple) and len(status) == 3:
                    statuses = status[0]
                else:
                    statuses = status
                    
                frame = self.drawer.draw_detections(frame, boxes, statuses, model_type)
            else:
                status = "nothing"

            # Отрисовка лэндмарков
            if self.show_landmarks and pose_results is not None:
                frame = self.drawer.draw_landmarks(frame, pose_results)

        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}", exc_info=True)
            status = False
            
        return frame, status

    def draw_landmarks(self, frame, pose_results, face_results):
        try:
            if pose_results is None and face_results is None:
                return frame
                
            # Проверяем, что есть что рисовать
            has_pose = pose_results is not None and hasattr(pose_results, 'pose_landmarks')
            has_face = face_results is not None and hasattr(face_results, 'multi_face_landmarks')
            
            if not has_pose and not has_face:
                return frame
                
            image_to_draw = frame.copy()
            draw_landmarks(image_to_draw, pose_results, face_results)
            return image_to_draw
        except Exception as e:
            self.logger.error(f"Landmark drawing error: {str(e)}")
            return frame

    def _check_compliance(self, boxes, pose_results, frame_shape, model_type):
        if 'siz' not in self.detectors or self.detectors['siz'] is None:
            self.logger.warning("SIZ detector not initialized")
            return [], 0, {}
            
        try:
            class_names = self.detectors['yolo'].class_names.get(model_type, [])
            statuses, people_count, detected_siz = self.detectors['siz'].check_items(
                boxes, pose_results, frame_shape, class_names
            )
            self.logger.debug(f"Compliance check result: {statuses}, people: {people_count}, detected: {detected_siz}")
            
            if hasattr(statuses, 'tolist'):
                return statuses.tolist(), people_count, detected_siz
            elif isinstance(statuses, (list, tuple)):
                return list(statuses), people_count, detected_siz
            return statuses, people_count, detected_siz
        except Exception as e:
            self.logger.error(f"Compliance check error: {str(e)}")
            return [], 0, {}

    def convert_to_qimage(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        return QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)

    def toggle_landmarks(self, state):
        self.show_landmarks = state
        self.logger.info(f"Landmarks visibility: {'ON' if state else 'OFF'}")