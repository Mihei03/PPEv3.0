class SIZDetector:
    def detect_multiple(self, pose_results, face_results, yolo_boxes, image_shape):
        """Проверка положения каждого обнаруженного СИЗ"""
        if yolo_boxes is None or len(yolo_boxes.xyxy) == 0:
            return []
            
        boxes = yolo_boxes.xyxy.cpu().numpy()
        classes = yolo_boxes.cls.cpu().numpy()
        statuses = []
        
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            class_id = int(classes[i])
            
            # Проверяем только определенные классы (например, очки)
            if class_id == 0:  # Пример для очков
                on_face = self._check_on_face(x1, y1, x2, y2, face_results, image_shape)
                statuses.append(on_face)
            else:
                # Для других классов считаем что они надеты правильно
                statuses.append(True)
                
        return statuses
        
    def _check_on_face(self, x1, y1, x2, y2, face_results, image_shape):
        """Проверка находится ли объект на лице"""
        if not face_results.multi_face_landmarks:
            return False
            
        h, w = image_shape[:2]
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        for face_landmarks in face_results.multi_face_landmarks:
            # Получаем координаты лица
            xs = [lm.x * w for lm in face_landmarks.landmark]
            ys = [lm.y * h for lm in face_landmarks.landmark]
            face_left, face_right = min(xs), max(xs)
            face_top, face_bottom = min(ys), max(ys)
            
            # Проверяем находится ли центр в области лица
            if (face_left < center_x < face_right and 
                face_top < center_y < face_bottom):
                return True
                
        return False