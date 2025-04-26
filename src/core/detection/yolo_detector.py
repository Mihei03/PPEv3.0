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
        try:
            if not os.path.exists(model_info['pt_file']):
                raise FileNotFoundError(f"Файл модели {model_info['pt_file']} не найден")
                
            if not os.path.exists(model_info['yaml_file']):
                raise FileNotFoundError(f"Конфиг {model_info['yaml_file']} не найден")
            
            model = YOLO(model_info['pt_file'])
            
            # Загрузка классов из YAML
            with open(model_info['yaml_file']) as f:
                data = yaml.safe_load(f)
                if 'names' not in data:
                    raise ValueError("YAML файл не содержит ключа 'names'")
                self.class_names[model_type] = data['names']  # Убедитесь, что это список
            
            self.models[model_type] = model
            self.current_model_name = model_type
            self.logger.info(f"Модель {model_type} успешно загружена. Классы: {self.class_names[model_type]}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели {model_type}: {str(e)}", exc_info=True)
            return False
    
    def detect(self, frame, model_type, statuses=None):
        if model_type not in self.models:
            return frame, None
            
        results = self.models[model_type](frame, verbose=False)
        
        if len(results[0].boxes) == 0:
            return frame, None
        
        boxes = results[0].boxes
        
        # Явное преобразование статусов
        if statuses is not None:
            if hasattr(statuses, '__iter__') and not isinstance(statuses, (str, bool)):
                statuses = [bool(s) for s in statuses]  # Преобразуем каждый элемент
        
        if statuses is not None:
            frame = self._draw_custom_boxes(frame, boxes.xyxy.cpu().numpy(), 
                                        boxes.conf.cpu().numpy(), 
                                        boxes.cls.cpu().numpy().astype(int),
                                        statuses, model_type)
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