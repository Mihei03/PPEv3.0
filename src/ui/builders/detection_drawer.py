import cv2
import mediapipe as mp
import numpy as np
from core.utils.logger import AppLogger
from core.utils.drawing_utils import draw_landmarks  # Импорт оригинальной функции

class DetectionDrawer:
    def __init__(self):
        self.logger = AppLogger.get_logger()
        self.detectors = {}
        # Инициализация стилей MediaPipe
        self.drawing_spec = mp.solutions.drawing_utils.DrawingSpec(
            color=(0, 255, 0), thickness=1, circle_radius=1
        )

    def set_detectors(self, yolo, siz):
        self.detectors['yolo'] = yolo
        self.detectors['siz'] = siz

    def draw_detections(self, frame, boxes, statuses, model_type):
        if boxes is None or not hasattr(boxes, 'xyxy'):
            return frame
            
        class_names = self.detectors['yolo'].class_names.get(model_type, [])
        
        # Явное преобразование статусов
        if statuses == "nothing":
            statuses = []
        elif isinstance(statuses, (bool, int, float)):
            statuses = [bool(statuses)] * len(boxes.xyxy)
        elif hasattr(statuses, '__iter__'):
            statuses = [bool(s) if not isinstance(s, str) else False for s in statuses]
        else:
            statuses = [False] * len(boxes.xyxy)
        
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
                
        return frame

    def draw_landmarks(self, frame, pose_results, face_results):
        """Используем оригинальную функцию из drawing_utils.py"""
        try:
            if pose_results is None and face_results is None:
                return frame
                
            # Создаем копию изображения для рисования
            image_to_draw = frame.copy()
            
            # Используем оригинальную функцию
            draw_landmarks(image_to_draw, pose_results, face_results)
            
            return image_to_draw
        except Exception as e:
            self.logger.error(f"Landmark drawing error: {str(e)}")
            return frame