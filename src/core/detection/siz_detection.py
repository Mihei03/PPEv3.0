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
                'head_points': [0, 1, 2, 5, 7, 8],  # Точки головы из позы
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
                'head_points': [0, 1, 2, 3, 4, 5, 7, 8],  # Оптимизированный набор точек
                'min_coverage': 0.25,
                'min_covered_points': 2,
                'expand_ratio': {
                    'side': 0.1,
                    'top': 0.5,
                    'bottom': 0.4
                }
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

    def check_items(self, boxes, pose_results, frame_shape, class_names):
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
                        status = bool(self._check_glasses(box, pose_results, w, h))
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

    def _check_glasses(self, box, pose_results, img_w, img_h):
        """Проверка положения очков по точкам головы"""
        if not pose_results or not hasattr(pose_results, 'pose_landmarks'):
            return False
            
        x1, y1, x2, y2 = map(int, box.cpu().numpy())
        rect = (x1, y1, x2, y2)
        
        covered = sum(
            1 for i in self.params['glasses']['head_points']
            if self._is_landmark_covered(pose_results.pose_landmarks.landmark[i], rect, img_w, img_h)
        )
        return (covered / len(self.params['glasses']['head_points'])) >= self.params['glasses']['min_coverage']

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
        """Проверка каски с использованием параметров из конфигурации"""
        if not pose_results or not hasattr(pose_results, 'pose_landmarks'):
            return False

        # Получаем параметры из конфигурации
        params = self.params['helmet']
        expand_ratio = params.get('expand_ratio', {'side': 0.15, 'top': 0.15, 'bottom': 0.15})  # Значения по умолчанию

        # Расширяем bounding box каски в соответствии с параметрами
        x1, y1, x2, y2 = map(int, box.cpu().numpy())
        width = x2 - x1
        height = y2 - y1
        expanded_box = (
            max(0, x1 - int(width * expand_ratio['side'])),
            max(0, y1 - int(height * expand_ratio['top'])),
            min(img_w, x2 + int(width * expand_ratio['side'])),
            min(img_h, y2 + int(height * expand_ratio['bottom']))
        )

        landmarks = pose_results.pose_landmarks.landmark

        # Проверка по точкам головы из конфигурации
        head_points = params.get('head_points', [0, 1, 2, 3, 4, 5, 7, 8])
        available_points = [i for i in head_points if i < len(landmarks)]

        if available_points:
            covered = sum(
                1 for i in available_points
                if self._is_landmark_covered(landmarks[i], expanded_box, img_w, img_h)
            )
            coverage_ratio = covered / len(available_points)
            min_coverage = params.get('min_coverage', 0.25)
            min_covered_points = params.get('min_covered_points', 2)

            if coverage_ratio >= min_coverage and covered >= min_covered_points:
                return True

        # Дополнительная проверка по расчетным точкам головы (если основная проверка не прошла)
        try:
            # Нос (точка 0)
            nose = landmarks[0]
            # Левое ухо (точка 7)
            left_ear = landmarks[7] if 7 < len(landmarks) else None
            # Правое ухо (точка 8)
            right_ear = landmarks[8] if 8 < len(landmarks) else None

            if nose and left_ear and right_ear:
                # Рассчитываем центр головы
                head_center_x = (left_ear.x + right_ear.x) / 2
                head_center_y = (left_ear.y + right_ear.y) / 2

                # Оцениваем размер головы
                head_width = abs(left_ear.x - right_ear.x) * img_w
                head_height = abs(nose.y - head_center_y) * img_h * 1.8  # Эмпирический коэффициент

                # Рассчитываем область лба (верхняя часть головы)
                forehead_top_x = head_center_x * img_w
                forehead_top_y = (nose.y - head_height * 0.3) * img_h

                # Проверяем, попадает ли эта точка в расширенный bounding box каски
                if (expanded_box[0] <= forehead_top_x <= expanded_box[2] and
                    expanded_box[1] <= forehead_top_y <= expanded_box[3]):
                    return True

                # Дополнительно проверяем точки по бокам головы
                for ear_point in [left_ear, right_ear]:
                    ear_x = ear_point.x * img_w
                    ear_y = ear_point.y * img_h
                    if (expanded_box[0] <= ear_x <= expanded_box[2] and
                        expanded_box[1] <= ear_y <= expanded_box[3]):
                        return True
        except Exception as e:
            self.logger.warning(f"Ошибка расчета точек головы: {str(e)}")

        return False

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