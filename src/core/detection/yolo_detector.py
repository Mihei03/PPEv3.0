from ultralytics import YOLO
import cv2
import yaml
from core.utils.logger import AppLogger
import os 

class YOLODetector:
    def __init__(self):
        self.models = {}
        self.class_names = {}
        self.current_model_name = ""
        self.logger = AppLogger.get_logger()
        self.logger.info("Инициализирован новый экземпляр YOLODetector")

    def is_initialized(self):
        """Проверка инициализации детектора"""
        return hasattr(self, 'models') and self.models is not None

    def load_model(self, model_type, model_info):
        """Загружает модель по типу ('glasses' или 'ppe')"""
        try:
            # Проверка существования файлов
            if not os.path.exists(model_info['pt_file']):
                raise FileNotFoundError(f"Файл модели {model_info['pt_file']} не найден")
                
            if not os.path.exists(model_info['yaml_file']):
                raise FileNotFoundError(f"Конфиг {model_info['yaml_file']} не найден")
            
            # Загрузка модели
            model = YOLO(model_info['pt_file'])
            
            # Загрузка классов
            with open(model_info['yaml_file']) as f:
                data = yaml.safe_load(f)
                self.class_names[model_type] = data['names']
            
            self.models[model_type] = model
            self.current_model_name = model_type
            self.logger.info(f"Модель {model_type} успешно загружена. Классы: {self.class_names[model_type]}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели {model_type}: {str(e)}", exc_info=True)
            # Очищаем недозагруженную модель
            if model_type in self.models:
                del self.models[model_type]
            return False
    
    def detect(self, frame, model_type, statuses=None):
        if model_type not in self.models:
            return frame, None
            
        results = self.models[model_type](frame, verbose=False)
        
        if len(results[0].boxes) == 0:
            return frame, None
        
        boxes = results[0].boxes
        confidences = boxes.conf.cpu().numpy()
        class_ids = boxes.cls.cpu().numpy().astype(int)
        
        if statuses is not None:
            frame = self._draw_custom_boxes(frame, boxes.xyxy, confidences, class_ids, statuses, model_type)
        else:
            frame = results[0].plot()
        
        return frame, boxes

    def _draw_custom_boxes(self, frame, boxes, confidences, class_ids, statuses, model_type):
        """Кастомная отрисовка с цветами по статусу"""
        for box, conf, cls_id, status in zip(boxes, confidences, class_ids, statuses):
            x1, y1, x2, y2 = map(int, box)
            color = (0, 255, 0) if status else (0, 0, 255)  # Зеленый/красный
            
            # Рисуем bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Подпись с названием класса и confidence
            class_name = self.class_names[model_type][cls_id]
            label = f"{class_name} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return frame