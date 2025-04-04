from core.utils.logger import AppLogger
import numpy as np

class SIZDetector:
    def __init__(self):
        self.logger = AppLogger.get_logger()
        self._setup_thresholds()
        
    def _setup_thresholds(self):
        """Конфигурационные параметры для проверок"""
        self.params = {
            'glasses': {
                'eye_points': {
                    'left': [33, 7, 163, 144],
                    'right': [263, 249, 390, 373]
                },
                'min_coverage': 0.7
            },
            'glove': {
                'hand_points': {
                    'left': [15, 17, 19, 21],  # Точки левой кисти MediaPipe Pose
                    'right': [16, 18, 20, 22]   # Точки правой кисти
                },
                'min_coverage': 0.6  # 60% точек должны быть покрыты
            },
            'helmet': {
                'head_points': [0, 1, 2, 5, 7, 8],  # Точки головы
                'min_coverage': 0.7  # 70% покрытия
            },
            'pants': {
                'leg_points': {
                    'left': [25, 27, 29, 31],  # Левая нога
                    'right': [26, 28, 30, 32]   # Правая нога
                },
                'min_coverage': 0.5  # 50% покрытия
            },
            'vest': {
                'body_points': [11, 12, 23, 24],  # Плечи и таз
                'min_points': 3  # Должен покрывать 3 из 4 точек
            }
        }

    def check_items(self, boxes, pose_results, face_results, frame_shape, class_names):
        """Проверка объектов с полной защитой от ошибок"""
        try:
            # Проверка входных данных
            if boxes is None or not hasattr(boxes, 'xyxy') or len(boxes.xyxy) == 0:
                return []
                
            if not isinstance(class_names, (list, dict)):
                class_names = []
                
            h, w = frame_shape[:2]
            statuses = []
            
            for i, (box, cls_id) in enumerate(zip(boxes.xyxy, boxes.cls)):
                try:
                    class_id = int(cls_id.cpu().numpy())
                    class_name = str(class_names[class_id]) if (class_names and class_id < len(class_names)) else str(class_id)
                    status = False
                    
                    if 'glass' in class_name.lower():
                        status = bool(self._check_glasses(box, face_results, w, h))  # Явное преобразование
                    elif 'glove' in class_name.lower():
                        status = bool(self._check_glove(box, pose_results, w, h))
                    elif 'helmet' in class_name.lower():
                        status = bool(self._check_helmet(box, pose_results, w, h))
                    elif 'pants' in class_name.lower():
                        status = bool(self._check_pants(box, pose_results, w, h))
                    elif 'vest' in class_name.lower():
                        status = bool(self._check_vest(box, pose_results, w, h))
                        
                    statuses.append(status)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing box {i}: {str(e)}")
                    statuses.append(False)
                    
            return statuses  # Гарантированно возвращаем список bool
            
        except Exception as e:
            self.logger.error(f"Check items error: {str(e)}")
            return []

    # Остальные методы класса остаются без изменений
    def _check_glasses(self, box, face_results, img_w, img_h):
        """Проверка положения очков"""
        if not face_results or not hasattr(face_results, 'multi_face_landmarks'):
            return False
            
        x1, y1, x2, y2 = map(int, box.cpu().numpy())
        rect = (x1, y1, x2, y2)
        
        for face in face_results.multi_face_landmarks:
            left_eye = self._check_eye_coverage(face, self.params['glasses']['eye_points']['left'], rect, img_w, img_h)
            right_eye = self._check_eye_coverage(face, self.params['glasses']['eye_points']['right'], rect, img_w, img_h)
            
            if left_eye and right_eye:
                return True
        return False

    def _check_glove(self, box, pose_results, img_w, img_h):
        """Проверка перчаток"""
        if not pose_results or not hasattr(pose_results, 'pose_landmarks'):
            return False

        x1, y1, x2, y2 = map(int, box.cpu().numpy())
        glove_rect = (x1, y1, x2, y2)
        
        # Проверяем обе руки
        left_covered = self._check_coverage(
            pose_results, 
            self.params['glove']['hand_points']['left'], 
            glove_rect, img_w, img_h
        )
        right_covered = self._check_coverage(
            pose_results,
            self.params['glove']['hand_points']['right'],
            glove_rect, img_w, img_h
        )
        
        return left_covered or right_covered

    def _check_helmet(self, box, pose_results, img_w, img_h):
        """Проверка каски"""
        if not pose_results or not hasattr(pose_results, 'pose_landmarks'):
            return False

        x1, y1, x2, y2 = map(int, box.cpu().numpy())
        helmet_rect = (x1, y1, x2, y2)
        
        covered = sum(
            1 for i in self.params['helmet']['head_points']
            if self._is_landmark_covered(pose_results.pose_landmarks.landmark[i], helmet_rect, img_w, img_h)
        )
        return (covered / len(self.params['helmet']['head_points'])) >= self.params['helmet']['min_coverage']
    
    def _check_pants(self, box, pose_results, img_w, img_h):
        """Проверка защитных штанов"""
        if not pose_results or not hasattr(pose_results, 'pose_landmarks'):
            return False

        x1, y1, x2, y2 = map(int, box.cpu().numpy())
        pants_rect = (x1, y1, x2, y2)
        
        # Проверяем обе ноги
        left_covered = self._check_coverage(
            pose_results,
            self.params['pants']['leg_points']['left'],
            pants_rect, img_w, img_h
        )
        right_covered = self._check_coverage(
            pose_results,
            self.params['pants']['leg_points']['right'],
            pants_rect, img_w, img_h
        )
        
        return left_covered or right_covered
    
    def _check_vest(self, box, pose_results, img_w, img_h):
        """Проверка жилета"""
        if not pose_results or not hasattr(pose_results, 'pose_landmarks'):
            return False

        x1, y1, x2, y2 = map(int, box.cpu().numpy())
        vest_rect = (x1, y1, x2, y2)
        
        covered = sum(
            1 for i in self.params['vest']['body_points']
            if self._is_landmark_covered(pose_results.pose_landmarks.landmark[i], vest_rect, img_w, img_h)
        )
        return covered >= self.params['vest']['min_points']

    def _check_eye_coverage(self, face_landmarks, eye_points, rect, img_w, img_h):
        """Проверка покрытия глаза"""
        covered = sum(
            1 for i in eye_points
            if self._is_landmark_covered(face_landmarks.landmark[i], rect, img_w, img_h)
        )
        return (covered / len(eye_points)) >= self.params['glasses']['min_coverage']

    def _check_coverage(self, pose_results, points, rect, img_w, img_h):
        """Проверка покрытия для набора точек"""
        covered = sum(
            1 for i in points
            if self._is_landmark_covered(pose_results.pose_landmarks.landmark[i], rect, img_w, img_h)
        )
        return (covered / len(points)) >= 0.5  # Базовый порог покрытия
    
    def _is_landmark_covered(self, landmark, rect, img_w, img_h):
        """Проверка покрытия конкретной точки"""
        x = landmark.x * img_w
        y = landmark.y * img_h
        return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]