import cv2
import mediapipe as mp

class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def detect(self, image):
        """Обнаружение ключевых точек тела."""
        # Конвертация изображения в RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        # Обнаружение ключевых точек тела
        results = self.pose.process(image_rgb)

        # Возвращаем результаты
        return results