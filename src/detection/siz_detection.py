import cv2
import numpy as np

class SIZDetector:
    def __init__(self):
        # Параметры для проверки (можно настраивать)
        self.glasses_eye_threshold = 0.7  # Покрытие глаз для очков
        self.helmet_head_threshold = 0.6  # Покрытие головы для каски
        
    def check_glasses(self, boxes, face_results, image_shape):
            if not hasattr(face_results, 'multi_face_landmarks'):
                return [False] * len(boxes.xyxy) if boxes else []
            """Проверка положения каждой пары очков отдельно"""
            statuses = []
            if not face_results.multi_face_landmarks:
                return [False] * len(boxes.xyxy)
                
            h, w = image_shape[:2]
            
            for box in boxes.xyxy:
                x1, y1, x2, y2 = map(int, box.cpu().numpy())
                glasses_rect = (x1, y1, x2, y2)
                status = False
                
                for face_landmarks in face_results.multi_face_landmarks:
                    # Получаем координаты глаз (MediaPipe Face Mesh)
                    left_eye = face_landmarks.landmark[33]
                    right_eye = face_landmarks.landmark[263]
                    
                    # Проверяем покрытие глаз
                    left_in = self._point_in_rect(left_eye.x * w, left_eye.y * h, glasses_rect)
                    right_in = self._point_in_rect(right_eye.x * w, right_eye.y * h, glasses_rect)
                    
                    if left_in and right_in:
                        status = True
                        break
                        
                statuses.append(status)
                
            return statuses
        
    def check_ppe(self, boxes, pose_results, image_shape):
        """Проверка других СИЗ (каска, жилет и т.д.)"""
        statuses = []
        if not pose_results.pose_landmarks:
            return [False] * len(boxes.xyxy)
            
        h, w = image_shape[:2]
        
        for box, cls in zip(boxes.xyxy, boxes.cls):
            x1, y1, x2, y2 = map(int, box.cpu().numpy())
            class_id = int(cls.cpu().numpy())
            status = False
            
            if class_id == 1:  # helmet
                status = self._check_helmet(x1, y1, x2, y2, pose_results, h, w)
            elif class_id == 2:  # vest
                status = self._check_vest(x1, y1, x2, y2, pose_results, h, w)
            # ... другие классы
            
            statuses.append(status)
            
        return statuses
        
    def _point_in_rect(self, x, y, rect):
        """Проверяет, находится ли точка (x,y) внутри прямоугольника"""
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2
        
    def _check_helmet(self, x1, y1, x2, y2, pose_results, h, w):
        """Проверка каски"""
        head_top = pose_results.pose_landmarks.landmark[0].y * h  # Нос (верх головы)
        helmet_center = (y1 + y2) / 2
        return helmet_center < head_top + 50  # Каска должна быть выше носа
        
    def _check_vest(self, x1, y1, x2, y2, pose_results, h, w):
        """Проверка жилета"""
        left_shoulder = pose_results.pose_landmarks.landmark[11]
        right_shoulder = pose_results.pose_landmarks.landmark[12]
        
        # Жилет должен покрывать оба плеча
        left_covered = self._point_in_rect(left_shoulder.x * w, left_shoulder.y * h, (x1, y1, x2, y2))
        right_covered = self._point_in_rect(right_shoulder.x * w, right_shoulder.y * h, (x1, y1, x2, y2))
        
        return left_covered and right_covered