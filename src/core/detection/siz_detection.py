from core.utils.logger import AppLogger
import numpy as np

class SIZDetector:
    def __init__(self):
        self.logger = AppLogger.get_logger()
        self._setup_thresholds()
        
    def _setup_thresholds(self):
        """Обновленные параметры для проверок с учетом точных соотношений"""
        self.params = {
            'glasses': {
                'head_points': [0, 1, 2],  # Нос (0), левый глаз (1), правый глаз (2)
                'min_coverage': 0.5,  
                'size_ratio': (0.2, 2.0)  # Более широкий диапазон
            },
            'glove': {
                'hand_points': {'left': 9, 'right': 10},  # Запястья (9 - левое, 10 - правое) - COCO
                'min_distance': 0.2,
                'min_confidence': 0.3,
                'expand_ratio': 0.3  # Коэффициент расширения bounding box
            },
            'helmet': {
                'head_points': [0, 1, 2, 3, 4],  # Нос, глаза, уши
                'min_coverage': 0.3,
                'size_ratio': (0.7, 3.0),  # Более широкий диапазон размеров
                'expand_down_ratio': 3,  # Сильное расширение вниз
                'min_covered_points': 1  # Хотя бы одна точка должна быть внутри
            },
            'pants': {
                'leg_points': [13, 14, 15, 16],  # Колени (13-14), лодыжки (15-16) - COCO
                'min_coverage': 0.4,
                'height_ratio': 0.3
            },
            'vest': {
                'body_points': [5, 6, 11, 12],  # Плечи (5-6), бедра (11-12) - COCO
                'min_points': 3,
                'min_coverage': 0.4
            }
        }

    def check_items(self, boxes, pose_results, frame_shape, class_names):
        self.logger.debug(f"Checking items with class_names: {class_names}")
        try:
            if boxes is None or len(boxes.xyxy) == 0:
                self.logger.debug("No boxes detected")
                return [], 0, {}

            # Подсчет людей в кадре
            people_count = 0
            if pose_results and hasattr(pose_results, 'keypoints'):
                people_count = len(pose_results.keypoints.xy)

            statuses = []
            required_siz = {}  # Словарь для отслеживания необходимых СИЗ
            detected_siz = {}  # Словарь для отслеживания обнаруженных СИЗ

            boxes_np = boxes.xyxy.cpu().numpy()
            cls_ids = boxes.cls.cpu().numpy()
            
            # Инициализация словарей для каждого типа СИЗ
            for class_name in class_names:
                if any(siz_type in class_name.lower() for siz_type in ['glasses', 'glove', 'helmet', 'pants', 'vest']):
                    required_siz[class_name] = people_count
                    detected_siz[class_name] = 0

            for i, (box, cls_id) in enumerate(zip(boxes_np, cls_ids)):
                try:
                    class_name = class_names[int(cls_id)] if class_names else str(cls_id)
                    status = False
                    
                    if pose_results and hasattr(pose_results, 'keypoints'):
                        person_idx = self._find_best_person_match(box, pose_results)
                        if person_idx is not None:
                            kpts = pose_results.keypoints.xy[person_idx].cpu().numpy()
                            if 'glass' in class_name.lower():
                                status = self._check_glasses(box, kpts)
                            elif 'glove' in class_name.lower():
                                status = self._check_glove(box, kpts, frame_shape[1], frame_shape[0])
                            elif 'helmet' in class_name.lower():
                                status = self._check_helmet(box, pose_results, frame_shape[1], frame_shape[0])
                            elif 'pants' in class_name.lower():
                                status = self._check_pants(box, kpts)
                            elif 'vest' in class_name.lower():
                                status = self._check_vest(box, kpts)
                            
                            # Увеличиваем счетчик обнаруженных СИЗ
                            if class_name in detected_siz:
                                detected_siz[class_name] += 1
                    
                    statuses.append(status)
                except Exception as e:
                    self.logger.warning(f"Error processing box {i}: {str(e)}")
                    statuses.append(False)
                    
            return statuses, people_count, detected_siz
        except Exception as e:
            self.logger.error(f"Check items error: {str(e)}")
            return [], 0, {}

    def _check_glove(self, box, kpts, img_w, img_h):
        """Проверка перчаток с увеличенной областью распознавания"""
        params = self.params['glove']
        
        try:
            x1, y1, x2, y2 = map(int, box)
            width = x2 - x1
            height = y2 - y1
            
            # Расширяем bounding box перчатки
            expanded_box = (
                max(0, x1 - int(width * params['expand_ratio'])),
                max(0, y1 - int(height * params['expand_ratio'])),
                min(img_w, x2 + int(width * params['expand_ratio'])),
                min(img_h, y2 + int(height * params['expand_ratio']))
            )

            # Проверяем обе руки
            left_hand_idx = params['hand_points']['left']
            right_hand_idx = params['hand_points']['right']
            
            left_covered = (left_hand_idx < len(kpts) and 
                           kpts[left_hand_idx][0] > 0 and 
                           self._is_point_covered(kpts[left_hand_idx], expanded_box))
            
            right_covered = (right_hand_idx < len(kpts) and 
                            kpts[right_hand_idx][0] > 0 and 
                            self._is_point_covered(kpts[right_hand_idx], expanded_box))
            
            return left_covered or right_covered
        except Exception as e:
            self.logger.error(f"Glove check error: {str(e)}")
            return False

    def _check_helmet(self, box, pose_results, img_w, img_h):
        """Проверка каски с учетом точного положения относительно головы"""
        params = self.params['helmet']
        
        if not pose_results or not hasattr(pose_results, 'keypoints'):
            return False

        try:
            # Координаты bounding box шлема
            x1, y1, x2, y2 = map(int, box)
            helmet_width = x2 - x1
            helmet_height = y2 - y1
            helmet_center = ((x1 + x2) / 2, (y1 + y2) / 2)
            
            # Расширяем bounding box для проверки точек головы
            expanded_box = (
                max(0, x1 - int(helmet_width * 0.3)),  # Расширение по бокам
                max(0, y1 - int(helmet_height * 0.5)),  # Расширение вверх
                min(img_w, x2 + int(helmet_width * 0.3)),  # Расширение по бокам
                min(img_h, y2 + int(helmet_height * 1.5))  # Расширение вниз
            )
            
            # Находим соответствующего человека
            kpts = pose_results.keypoints.xy.cpu().numpy()
            person_idx = self._find_best_person_match(box, pose_results)
            
            if person_idx is None:
                return False
                
            kpts = kpts[person_idx]
            head_points = []
            
            # Собираем видимые точки головы
            for i in params['head_points']:
                if i < len(kpts) and kpts[i][0] > 0 and kpts[i][1] > 0:
                    head_points.append(kpts[i])
            
            if not head_points:
                return False
                
            # 1. Проверяем покрытие точек головы расширенным bounding box
            points_inside = sum(
                1 for pt in head_points
                if (expanded_box[0] <= pt[0] <= expanded_box[2] and
                    expanded_box[1] <= pt[1] <= expanded_box[3]))
            
            # 2. Проверяем положение шлема относительно головы
            avg_head = np.mean(head_points, axis=0)
            head_top = min(pt[1] for pt in head_points)  # Самая верхняя точка головы
            
            # Максимальное допустимое расстояние между низом шлема и верхом головы
            max_allowed_distance = helmet_height * 0.1
            
            # Проверяем:
            # 1. Низ шлема должен быть не слишком далеко от верха головы
            # 2. Центр шлема должен быть выше средней точки головы
            distance_ok = (y2 - head_top) <= max_allowed_distance
            position_ok = helmet_center[1] < avg_head[1]
            
            # 3. Проверяем соотношение размеров
            head_width = max(pt[0] for pt in head_points) - min(pt[0] for pt in head_points)
            size_ratio = helmet_width / (head_width + 1e-6)
            size_ok = params['size_ratio'][0] <= size_ratio <= params['size_ratio'][1]
            
            # Комбинированная проверка
            condition1 = points_inside >= params['min_covered_points']
            condition2 = distance_ok and position_ok
            
            self.logger.debug(
                f"Helmet check - points inside: {points_inside}, "
                f"head top: {head_top:.1f}, helmet bottom: {y2:.1f}, "
                f"distance: {y2 - head_top:.1f} (max {max_allowed_distance:.1f}), "
                f"position: {'OK' if position_ok else 'FAIL'}, "
                f"size ratio: {size_ratio:.2f}, "
                f"condition1: {condition1}, condition2: {condition2}"
            )
            
            return condition1 and condition2 and size_ok
            
        except Exception as e:
            self.logger.error(f"Helmet check error: {str(e)}")
            return False

    # Остальные методы остаются без изменений
    def _check_pants(self, box, kpts):
        """Проверка штанов с покрытием ног"""
        params = self.params['pants']
        
        try:
            leg_points = []
            for i in params['leg_points']:
                if i < len(kpts) and kpts[i][0] > 0:
                    leg_points.append(kpts[i])
            
            if len(leg_points) < 2:
                self.logger.debug("Not enough visible leg points for pants check")
                return False
            
            covered = sum(self._is_point_covered(pt, box) for pt in leg_points)
            coverage = covered / len(leg_points)
            
            person_height = self._estimate_person_size(kpts)
            box_height = box[3] - box[1]
            height_ratio = box_height / (person_height + 1e-6)
            
            self.logger.debug(f"Pants check - coverage: {coverage:.2f}, height_ratio: {height_ratio:.2f}")
            
            return coverage >= params['min_coverage'] and height_ratio >= params['height_ratio']
        except Exception as e:
            self.logger.error(f"Pants check error: {str(e)}")
            return False
    
    def _check_vest(self, box, kpts):
        """Проверка жилета с покрытием плеч и груди"""
        params = self.params['vest']
        
        try:
            body_points = []
            for i in params['body_points']:
                if i < len(kpts) and kpts[i][0] > 0:
                    body_points.append(kpts[i])
            
            if len(body_points) < params['min_points']:
                self.logger.debug("Not enough visible body points for vest check")
                return False
            
            covered = sum(self._is_point_covered(pt, box) for pt in body_points)
            coverage = covered / len(body_points)
            
            self.logger.debug(f"Vest check - coverage: {coverage:.2f}")
            
            return coverage >= params['min_coverage']
        except Exception as e:
            self.logger.error(f"Vest check error: {str(e)}")
            return False
    
    def _check_glasses(self, box, kpts):
        """Проверка очков с учетом размера и положения"""
        params = self.params['glasses']
        
        try:
            head_points = []
            for i in params['head_points']:
                if i < len(kpts) and kpts[i][0] > 0 and kpts[i][1] > 0:
                    head_points.append(kpts[i])
            
            if len(head_points) < 2:
                self.logger.debug("Not enough visible head points for glasses check")
                return False
                
            head_points = np.array(head_points)
            
            covered = sum(self._is_point_covered(pt, box) for pt in head_points)
            coverage = covered / len(head_points)
            
            head_width = np.max(head_points[:,0]) - np.min(head_points[:,0])
            box_width = box[2] - box[0]
            size_ratio = box_width / (head_width + 1e-6)
            
            size_ok = params['size_ratio'][0] <= size_ratio <= params['size_ratio'][1]
            
            result = (coverage >= params['min_coverage']) or size_ok
            
            self.logger.debug(f"Glasses check - coverage: {coverage:.2f}, size_ratio: {size_ratio:.2f}, result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Glasses check error: {str(e)}")
            return False

    # Остальные вспомогательные методы без изменений
    def _find_best_person_match(self, box, pose_results):
        """Находит наиболее подходящего человека с учетом нескольких факторов"""
        best_match = None
        best_score = -1
        
        for i, kpts in enumerate(pose_results.keypoints.xy.cpu().numpy()):
            visible_points = sum(1 for kpt in kpts if kpt[0] > 0 and kpt[1] > 0)
            if visible_points < 5:
                continue
                
            body_center = self._get_body_center(kpts)
            box_center = ((box[0] + box[2])/2, (box[1] + box[3])/2)
            
            distance = np.sqrt((body_center[0]-box_center[0])**2 + (body_center[1]-box_center[1])**2)
            
            person_size = self._estimate_person_size(kpts)
            norm_distance = distance / (person_size + 1e-6)
            
            score = 1.0 / (1.0 + norm_distance)
            
            if score > best_score:
                best_score = score
                best_match = i
                
        return best_match

    def _get_body_center(self, kpts):
        """Вычисляет центр тела по видимым ключевым точкам"""
        visible = [kpt for kpt in kpts if kpt[0] > 0 and kpt[1] > 0]
        if not visible:
            return (0, 0)
        return np.mean(visible, axis=0)

    def _estimate_person_size(self, kpts):
        """Оценивает размер человека по ключевым точкам"""
        visible = [kpt for kpt in kpts if kpt[0] > 0 and kpt[1] > 0]
        if len(visible) < 2:
            return 0
        return np.max([np.linalg.norm(a-b) for a in visible for b in visible])

    def _is_point_covered(self, point, box):
        """Проверяет, покрыта ли точка bounding box"""
        return (box[0] <= point[0] <= box[2] and 
                box[1] <= point[1] <= box[3])

    def _is_landmark_covered(self, landmark, box, img_w, img_h):
        """Проверяет, покрыт ли landmark bounding box"""
        x = landmark.x * img_w
        y = landmark.y * img_h
        return (box[0] <= x <= box[2] and 
                box[1] <= y <= box[3])

    def _box_intersection(self, box1, box2):
        """Вычисляет площадь пересечения двух bounding box"""
        dx = min(box1[2], box2[2]) - max(box1[0], box2[0])
        dy = min(box1[3], box2[3]) - max(box1[1], box2[1])
        return dx * dy if dx > 0 and dy > 0 else 0

    def _expand_box(self, box, ratio):
        """Расширяет bounding box на заданный процент"""
        w = box[2] - box[0]
        h = box[3] - box[1]
        return [
            box[0] - w * ratio,
            box[1] - h * ratio,
            box[2] + w * ratio,
            box[3] + h * ratio
        ]
    
    def get_missing_siz_areas(self, pose_results, frame_shape, detected_siz, required_siz, class_names):
        """Возвращает области, где должны быть СИЗ, но их нет"""
        missing_areas = []
        
        if pose_results is None or not hasattr(pose_results, 'keypoints'):
            return missing_areas
        
        try:
            # Проверяем каждый тип СИЗ
            for siz_type in ['glasses', 'glove', 'helmet', 'vest', 'pants']:
                # Проверяем, есть ли этот тип СИЗ в модели
                if not self._is_siz_in_model(siz_type, class_names):
                    continue
                    
                # Если этот тип СИЗ требуется, но не обнаружен
                required = required_siz.get(siz_type, 0)
                detected = detected_siz.get(siz_type, 0)
                
                if required > detected:
                    for person_idx in range(len(pose_results.keypoints.xy)):
                        kpts = pose_results.keypoints.xy[person_idx].cpu().numpy()
                        
                        # Определяем область для каждого типа СИЗ
                        if siz_type == 'glasses':
                            # Получаем точки глаз (левый и правый глаз)
                            left_eye_idx, right_eye_idx = 1, 2
                            left_eye = kpts[left_eye_idx] if left_eye_idx < len(kpts) and kpts[left_eye_idx][0] > 0 else None
                            right_eye = kpts[right_eye_idx] if right_eye_idx < len(kpts) and kpts[right_eye_idx][0] > 0 else None
                            
                            if left_eye is not None and right_eye is not None:
                                # Вычисляем центр между глазами
                                center_x = (left_eye[0] + right_eye[0]) / 2
                                center_y = (left_eye[1] + right_eye[1]) / 2
                                
                                # Ширина очков - расстояние между глазами + 20%
                                width = abs(left_eye[0] - right_eye[0]) * 1.4
                                
                                # Высота очков - пропорционально ширине
                                height = width * 0.4
                                
                                area = (
                                    int(max(0, center_x - width/2)),
                                    int(max(0, center_y - height/2)),
                                    int(min(frame_shape[1], center_x + width/2)),
                                    int(min(frame_shape[0], center_y + height/2))
                                )
                                missing_areas.append((area, siz_type))
                        
                        elif siz_type == 'helmet':
                            # Область над головой
                            head_points = [kpts[i] for i in [0,1,2,3,4] 
                                        if i < len(kpts) and kpts[i][0] > 0 and kpts[i][1] > 0]
                            if head_points:
                                x_coords = [pt[0] for pt in head_points]
                                y_coords = [pt[1] for pt in head_points]
                                x_center = sum(x_coords) / len(x_coords)
                                head_top = min(y_coords)
                                
                                # Размер каски примерно равен ширине головы
                                head_width = max(x_coords) - min(x_coords)
                                helmet_size = head_width * 1.2
                                
                                area = (
                                    int(max(0, x_center - helmet_size/2)),
                                    int(max(0, head_top - helmet_size)),
                                    int(min(frame_shape[1], x_center + helmet_size/2)),
                                    int(min(frame_shape[0], head_top))
                                )
                                missing_areas.append((area, siz_type))
                        
                        # Аналогично для других типов СИЗ
                        elif siz_type == 'glove':
                            # Для левой и правой руки отдельно
                            for hand_idx in [9, 10]:  # Индексы запястий в COCO
                                if hand_idx < len(kpts) and kpts[hand_idx][0] > 0:
                                    x, y = kpts[hand_idx]
                                    glove_size = 50  # Фиксированный размер для перчаток
                                    area = (
                                        int(max(0, x - glove_size/2)),
                                        int(max(0, y - glove_size/2)),
                                        int(min(frame_shape[1], x + glove_size/2)),
                                        int(min(frame_shape[0], y + glove_size/2))
                                    )
                                    missing_areas.append((area, siz_type))
                        
                        elif siz_type == 'vest':
                            # Область туловища
                            body_points = [kpts[i] for i in [5,6,11,12]  # Плечи и бедра
                                        if i < len(kpts) and kpts[i][0] > 0]
                            if len(body_points) >= 2:
                                x_coords = [pt[0] for pt in body_points]
                                y_coords = [pt[1] for pt in body_points]
                                x_center = sum(x_coords) / len(x_coords)
                                y_center = sum(y_coords) / len(y_coords)
                                width = max(x_coords) - min(x_coords)
                                height = max(y_coords) - min(y_coords)
                                
                                area = (
                                    int(max(0, x_center - width/2)),
                                    int(max(0, y_center - height/3)),
                                    int(min(frame_shape[1], x_center + width/2)),
                                    int(min(frame_shape[0], y_center + height/3))
                                )
                                missing_areas.append((area, siz_type))
                        
                        elif siz_type == 'pants':
                            # Получаем точки ног (бедра и колени)
                            left_hip_idx, right_hip_idx = 11, 12
                            left_knee_idx, right_knee_idx = 13, 14
                            
                            left_hip = kpts[left_hip_idx] if left_hip_idx < len(kpts) and kpts[left_hip_idx][0] > 0 else None
                            right_hip = kpts[right_hip_idx] if right_hip_idx < len(kpts) and kpts[right_hip_idx][0] > 0 else None
                            left_knee = kpts[left_knee_idx] if left_knee_idx < len(kpts) and kpts[left_knee_idx][0] > 0 else None
                            right_knee = kpts[right_knee_idx] if right_knee_idx < len(kpts) and kpts[right_knee_idx][0] > 0 else None
                            
                            if left_hip is not None and left_knee is not None:
                                # Левая нога
                                width = 40  # Фиксированная ширина для штанин
                                area_left = (
                                    int(max(0, left_hip[0] - width/2)),
                                    int(min(left_hip[1], left_knee[1])),
                                    int(min(frame_shape[1], left_hip[0] + width/2)),
                                    int(max(left_hip[1], left_knee[1]))
                                )
                                missing_areas.append((area_left, siz_type))
                                
                            if right_hip is not None and right_knee is not None:
                                # Правая нога
                                width = 40  # Фиксированная ширина для штанин
                                area_right = (
                                    int(max(0, right_hip[0] - width/2)),
                                    int(min(right_hip[1], right_knee[1])),
                                    int(min(frame_shape[1], right_hip[0] + width/2)),
                                    int(max(right_hip[1], right_knee[1]))
                                )
                                missing_areas.append((area_right, siz_type))
                        
            return missing_areas
        except Exception as e:
            self.logger.error(f"Error getting missing SIZ areas: {str(e)}")
            return []
    
    def _is_siz_in_model(self, siz_type, class_names):
        """Проверяет, есть ли данный тип СИЗ в загруженной модели"""
        siz_type = siz_type.lower()
        for class_name in class_names:
            if siz_type in class_name.lower():
                return True
        return False
