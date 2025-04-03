import cv2
import mediapipe as mp
from utils.logger import AppLogger
from src.utils.drawing_utils import draw_landmarks  # Импорт оригинальной функции

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
        
        for i, box in enumerate(boxes.xyxy):
            try:
                x1, y1, x2, y2 = map(int, box.cpu().numpy())
                status = statuses[i] if isinstance(statuses, list) and i < len(statuses) else statuses
                
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
            # Создаем копию изображения для рисования
            image_to_draw = frame.copy()
            
            # Используем оригинальную функцию
            draw_landmarks(image_to_draw, pose_results, face_results)
            
            return image_to_draw
        except Exception as e:
            self.logger.error(f"Landmark drawing error: {str(e)}")
            return frame