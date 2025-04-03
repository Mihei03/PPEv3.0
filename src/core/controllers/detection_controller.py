from core.detection.yolo_detector import YOLODetector
from core.detection.face_detection import FaceDetector
from core.detection.pose_detection import PoseDetector
from core.detection.siz_detection import SIZDetector

class DetectionController:
    def __init__(self):
        self.yolo = None
        self.face = None
        self.pose = None
        self.siz = None
        
    def setup_detectors(self):
        self.yolo = YOLODetector()
        self.face = FaceDetector()
        self.pose = PoseDetector()
        self.siz = SIZDetector()