from ultralytics import YOLO
import cv2
import yaml
import os

class YOLODetector:
    def __init__(self):
        self.model = None
        self.class_names = []
        self.current_model_name = ""
        
    def load_model(self, model_info):
        """Загружает модель из информации о папке"""
        self.model = None
        self.class_names = []
        
        try:
            # Загрузка модели
            self.model = YOLO(model_info['pt_file'])
            
            # Загрузка классов
            with open(model_info['yaml_file']) as f:
                data = yaml.safe_load(f)
                self.class_names = data.get('names', [])
            
            self.current_model_name = os.path.basename(model_info['path'])
            print(f"Загружена модель: {self.current_model_name}")
            print(f"Классы: {self.class_names}")
            return True
            
        except Exception as e:
            print(f"Ошибка загрузки модели: {str(e)}")
            self.model = None
            return False
    
    def detect(self, frame, siz_statuses=None):
        """Детекция объектов с цветовой индикацией"""
        if self.model is None:
            return frame, None
            
        results = self.model(frame, verbose=False)
        
        if len(results[0].boxes) == 0:
            return frame, None
            
        boxes = results[0].boxes.xyxy.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()
        
        for i, (box, cls, conf) in enumerate(zip(boxes, classes, confidences)):
            x1, y1, x2, y2 = map(int, box)
            class_id = int(cls)
            confidence = float(conf)
            
            # Определение цвета
            color = (0, 255, 0) if (siz_statuses and i < len(siz_statuses) and siz_statuses[i]) else (0, 0, 255)
            
            # Рисование bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Подпись
            label = f"{self.class_names[class_id]}: {confidence:.2f}" if class_id < len(self.class_names) else f"{class_id}: {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame, results[0].boxes