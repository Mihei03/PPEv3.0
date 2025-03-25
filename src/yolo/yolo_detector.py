from ultralytics import YOLO
import cv2
import yaml
from utils.logger import AppLogger

class YOLODetector:
    def __init__(self):
        self.models = {}
        self.class_names = {}  # Инициализация пустого списка
        self.current_model_name = ""
        self.logger = AppLogger.get_logger()

    def load_model(self, model_type, model_info):
        """Загружает модель по типу ('glasses' или 'ppe')"""
        try:
            model = YOLO(model_info['pt_file'])
            
            with open(model_info['yaml_file']) as f:
                data = yaml.safe_load(f)
                self.class_names[model_type] = data['names']
            
            self.models[model_type] = model
            self.logger.info(f"Загружена модель {model_type}. Классы: {self.class_names[model_type]}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели {model_type}: {str(e)}")
            return False
    
    def detect(self, frame, model_type, siz_statuses=None):
        if model_type not in self.models:
            return frame, None
            
        results = self.models[model_type](frame, verbose=False)
        if len(results[0].boxes) == 0:
            return frame, None
            
        boxes = results[0].boxes.xyxy.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()
        
        for i, (box, cls, conf) in enumerate(zip(boxes, classes, confidences)):
            x1, y1, x2, y2 = map(int, box)
            class_id = int(cls)
            confidence = float(conf)
            
            # Безопасное получение имени класса
            class_name = "unknown"
            if model_type in self.class_names:
                if 0 <= class_id < len(self.class_names[model_type]):
                    class_name = self.class_names[model_type][class_id]
            
            # Определение цвета
            color = (0, 255, 0) if (siz_statuses and i < len(siz_statuses) and siz_statuses[i]) else (0, 0, 255)
            
            # Рисование bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Подпись
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return frame, results[0].boxes