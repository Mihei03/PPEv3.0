from core.detection.yolo_detector import YOLODetector
from core.detection.pose_detection import PoseDetector
from core.detection.siz_detection import SIZDetector

class DetectionController:
    def __init__(self):
        self.yolo = None
        self.pose = None
        self.siz = None
        
    def setup_detectors(self):
        self.yolo = YOLODetector()
        self.pose = PoseDetector()
        self.siz = SIZDetector()