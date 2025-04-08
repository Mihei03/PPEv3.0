from ultralytics import YOLO
import cv2
from core.utils.logger import AppLogger

class PoseDetector:
    def __init__(self):
        self.logger = AppLogger.get_logger()
        self.model = YOLO('src/core/detection/key_points/yolo11n-pose.pt')  # Загружаем модель YOLO для поз
        self.logger.info("Инициализирован YOLOv11 Pose детектор")

    def detect(self, image):
        """Обнаружение ключевых точек тела с помощью YOLOv11 Pose."""
        try:
            # YOLOv11 возвращает результаты для всех людей в кадре
            results = self.model(image, verbose=False)
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"Ошибка детекции позы: {str(e)}")
            return None