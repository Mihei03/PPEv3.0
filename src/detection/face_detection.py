import cv2
import mediapipe as mp

class FaceDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    def detect(self, image):
        """Обнаружение ключевых точек лица."""
        # Конвертация изображения в RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_rgb.flags.writeable = False

        # Обнаружение ключевых точек лица
        results = self.face_mesh.process(image_rgb)

        # Возвращаем результаты
        return results