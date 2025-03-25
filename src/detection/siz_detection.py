from utils.logger import AppLogger

class SIZDetector:
    def __init__(self):
        # Параметры для проверки (можно настраивать)
        self.glasses_eye_threshold = 0.7  # Минимальное покрытие глаз для очков
        self.helmet_head_threshold = 0.6  # Минимальное покрытие головы для каски
        self.vest_min_points = 2         # Минимальное количество покрытых точек для жилета
        self.logger = AppLogger.get_logger()

    def check_glasses(self, boxes, face_results, image_shape):
        """Проверка очков с полной защитой от None"""
        try:
            # 1. Проверка на полное отсутствие данных
            if boxes is None:
                self.logger.debug("Нет данных о боксах (boxes = None)")
                return "nothing"
                
            # 2. Проверка структуры boxes
            if not hasattr(boxes, 'xyxy'):
                self.logger.warning(f"Некорректная структура boxes: {type(boxes)}")
                return "nothing"
                
            # 3. Проверка на пустые результаты
            if len(boxes.xyxy) == 0:
                self.logger.debug("Нет обнаруженных очков (пустой список boxes.xyxy)")
                return "nothing"
                
            # 4. Проверка face_results
            if face_results is None:
                self.logger.debug("Нет данных о лице (face_results = None)")
                return [False] * len(boxes.xyxy)
                
            # 5. Проверка структуры face_results
            if not hasattr(face_results, 'multi_face_landmarks'):
                self.logger.warning(f"Некорректная структура face_results: {type(face_results)}")
                return [False] * len(boxes.xyxy)
                
            # 6. Проверка на пустые landmarks
            if not face_results.multi_face_landmarks:
                self.logger.debug("Нет landmarks лица (пустой список multi_face_landmarks)")
                return [False] * len(boxes.xyxy)
                
            # Основная логика проверки
            h, w = image_shape[:2]
            statuses = []
            
            for box in boxes.xyxy:
                try:
                    x1, y1, x2, y2 = map(int, box.cpu().numpy())
                    glasses_rect = (x1, y1, x2, y2)
                    status = False
                    
                    for face_landmarks in face_results.multi_face_landmarks:
                        if not hasattr(face_landmarks, 'landmark'):
                            continue
                            
                        left_eye_covered = self._check_eye_coverage(face_landmarks, [33, 7, 163, 144], glasses_rect, w, h)
                        right_eye_covered = self._check_eye_coverage(face_landmarks, [263, 249, 390, 373], glasses_rect, w, h)
                        
                        if left_eye_covered and right_eye_covered:
                            status = True
                            break
                            
                    statuses.append(status)
                    
                except Exception as box_e:
                    self.logger.error(f"Ошибка обработки бокса: {str(box_e)}")
                    statuses.append(False)
                    
            return statuses
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка в check_glasses: {str(e)}")
            return "nothing"

    def _check_eye_coverage(self, face_landmarks, eye_points, glasses_rect, w, h):
        """Проверка покрытия одного глаза"""
        try:
            if not hasattr(face_landmarks, 'landmark'):
                return False
                
            covered = sum(
                1 for i in eye_points 
                if hasattr(face_landmarks.landmark[i], 'x') and 
                hasattr(face_landmarks.landmark[i], 'y') and
                self._point_in_rect(
                    face_landmarks.landmark[i].x * w,
                    face_landmarks.landmark[i].y * h,
                    glasses_rect
                )
            )
            return (covered / len(eye_points)) >= self.glasses_eye_threshold
        except:
            return False
    
    def check_ppe(self, boxes, pose_results, image_shape):
        """Проверка СИЗ (каски, жилеты)"""
        try:
            # Проверка входных данных
            if not self._validate_input(boxes, pose_results, require_pose=True):
                self.logger.debug("Нет данных для проверки СИЗ")
                return "nothing" if boxes is None else [False] * len(boxes.xyxy)
            
            h, w = image_shape[:2]
            statuses = []
            
            for box, cls in zip(boxes.xyxy, boxes.cls):
                x1, y1, x2, y2 = map(int, box.cpu().numpy())
                class_id = int(cls.cpu().numpy())
                status = False
                
                if class_id == 1:  # helmet
                    status = self._check_helmet(x1, y1, x2, y2, pose_results, h, w)
                elif class_id == 2:  # vest
                    status = self._check_vest(x1, y1, x2, y2, pose_results, h, w)
                
                statuses.append(status)
                
            return statuses
            
        except Exception as e:
            self.logger.error(f"Ошибка в check_ppe: {str(e)}")
            return "nothing" if boxes is None else [False] * len(boxes.xyxy)

    def _validate_input(self, boxes, results, require_face=False, require_pose=False):
        """Проверка валидности входных данных"""
        if boxes is None:
            return False
            
        if not hasattr(boxes, 'xyxy') or len(boxes.xyxy) == 0:
            return False
            
        if require_face and (results is None or not hasattr(results, 'multi_face_landmarks')):
            return False
            
        if require_pose and (results is None or not hasattr(results, 'pose_landmarks')):
            return False
            
        return True

    def _check_eyes_coverage(self, face_landmarks, glasses_rect, w, h):
        """Проверяет покрытие обоих глаз"""
        left_eye_points = [33, 7, 163, 144]
        right_eye_points = [263, 249, 390, 373]
        
        left_covered = sum(
            self._point_in_rect(face_landmarks.landmark[i].x * w,
                              face_landmarks.landmark[i].y * h,
                              glasses_rect)
            for i in left_eye_points
        ) / len(left_eye_points) >= self.glasses_eye_threshold
        
        right_covered = sum(
            self._point_in_rect(face_landmarks.landmark[i].x * w,
                              face_landmarks.landmark[i].y * h,
                              glasses_rect)
            for i in right_eye_points
        ) / len(right_eye_points) >= self.glasses_eye_threshold
        
        return left_covered and right_covered

    def _point_in_rect(self, x, y, rect):
        """Проверяет, находится ли точка (x,y) внутри прямоугольника"""
        x1, y1, x2, y2 = rect
        return x1 <= x <= x2 and y1 <= y <= y2
        
    def _check_helmet(self, x1, y1, x2, y2, pose_results, h, w):
        """Проверка каски"""
        try:
            head_points = [0, 1, 2, 5, 7, 8]
            covered_points = sum(
                self._point_in_rect(pose_results.pose_landmarks.landmark[i].x * w,
                                  pose_results.pose_landmarks.landmark[i].y * h,
                                  (x1, y1, x2, y2))
                for i in head_points
            )
            return (covered_points / len(head_points)) >= self.helmet_head_threshold
        except Exception as e:
            self.logger.warning(f"Ошибка проверки каски: {str(e)}")
            return False
            
    def _check_vest(self, x1, y1, x2, y2, pose_results, h, w):
        """Проверка жилета"""
        try:
            key_points = [11, 12, 23, 24]
            covered_points = sum(
                self._point_in_rect(pose_results.pose_landmarks.landmark[i].x * w,
                                  pose_results.pose_landmarks.landmark[i].y * h,
                                  (x1, y1, x2, y2))
                for i in key_points
            )
            return covered_points >= self.vest_min_points
        except Exception as e:
            self.logger.warning(f"Ошибка проверки жилета: {str(e)}")
            return False