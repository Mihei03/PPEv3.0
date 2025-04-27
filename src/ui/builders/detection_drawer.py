import cv2
import mediapipe as mp
import numpy as np
from core.utils.logger import AppLogger
from core.utils.drawing_utils import draw_landmarks  # Импорт оригинальной функции

class DetectionDrawer:
    def __init__(self):
        self.logger = AppLogger.get_logger()
        self.detectors = {}
        self.show_landmarks = False
        self.drawing_spec = mp.solutions.drawing_utils.DrawingSpec(
            color=(0, 255, 0), thickness=1, circle_radius=1
        )

    def set_show_landmarks(self, show):
        """Устанавливает флаг отображения ключевых точек"""
        self.show_landmarks = show

    def set_detectors(self, yolo, siz):
        self.detectors['yolo'] = yolo
        self.detectors['siz'] = siz

    def draw_detections(self, frame, boxes, statuses, model_type, pose_results=None, missing_areas=None):
        if boxes is None or not hasattr(boxes, 'xyxy'):
            self.logger.warning("No boxes to draw")
            # Рисуем отсутствующие СИЗ, даже если нет боксов
            if missing_areas:
                frame = self.draw_missing_siz(frame, missing_areas)
            # Рисуем ключевые точки, если включено
            if self.show_landmarks and pose_results:
                frame = self.draw_landmarks(frame, pose_results)
            return frame
            
        class_names = self.detectors['yolo'].class_names.get(model_type, [])
        
        if isinstance(statuses, str):  # "nothing"
            statuses = [False] * len(boxes.xyxy)
        elif isinstance(statuses, (bool, int, float)):
            statuses = [bool(statuses)] * len(boxes.xyxy)
        elif not hasattr(statuses, '__iter__'):
            statuses = [False] * len(boxes.xyxy)
        
        self.logger.debug(f"Drawing {len(boxes.xyxy)} boxes with statuses: {statuses}")
        
        for i, box in enumerate(boxes.xyxy):
            try:
                x1, y1, x2, y2 = map(int, box.cpu().numpy())
                status = bool(statuses[i]) if i < len(statuses) else False
                
                cls_id = int(boxes.cls[i].cpu().numpy()) if i < len(boxes.cls) else 0
                conf = float(boxes.conf[i].cpu().numpy()) if i < len(boxes.conf) else 0.0
                class_name = str(class_names[cls_id]) if (class_names and cls_id < len(class_names)) else f"Class {cls_id}"
                
                # Цвет зависит от статуса (True - зеленый, False - красный)
                color = (0, 255, 0) if status else (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                label = f"{class_name} {conf:.2f}"
                cv2.putText(frame, label, (x1, max(y1-10, 20)), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            except Exception as e:
                self.logger.warning(f"Error drawing box {i}: {str(e)}")
                continue
        
        if missing_areas:
            frame = self.draw_missing_siz(frame, missing_areas)
            
        # Рисуем ключевые точки, если включено
        if self.show_landmarks and pose_results is not None:
            frame = self.draw_landmarks(frame, pose_results)

        return frame

    def draw_landmarks(self, frame, pose_results):
        try:
            if pose_results is None or not hasattr(pose_results, 'keypoints'):
                return frame
                
            # Создаем копию кадра для рисования
            image_to_draw = frame.copy()
            image_with_landmarks = draw_landmarks(image_to_draw, pose_results)
            
            # Наложение обратно на исходный кадр
            cv2.addWeighted(image_with_landmarks, 0.7, frame, 0.3, 0, frame)
            return frame
        except Exception as e:
            self.logger.error(f"Landmark drawing error: {str(e)}")
            return frame
        
    def draw_missing_siz(self, frame, missing_areas):
        """Рисует красные прямоугольники для отсутствующих СИЗ"""
        if not missing_areas:
            return frame
            
        try:
            for area, siz_type in missing_areas:
                x1, y1, x2, y2 = area
                color = (0, 0, 255)  # Красный
                
                # Рисуем полупрозрачный прямоугольник
                overlay = frame.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)  # Заполненный
                alpha = 0.3  # Прозрачность
                frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
                
                # Рисуем контур
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # Подпись с типом отсутствующего СИЗ
                label = f"Missing {siz_type}"
                (label_width, label_height), _ = cv2.getTextSize(label, 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                
                # Фон для текста
                cv2.rectangle(frame, 
                    (x1, y1 - label_height - 10),
                    (x1 + label_width, y1 - 10),
                    color, -1)
                    
                # Текст
                cv2.putText(frame, label, 
                    (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
            return frame
        except Exception as e:
            self.logger.warning(f"Error drawing missing SIZ: {str(e)}")
            return frame