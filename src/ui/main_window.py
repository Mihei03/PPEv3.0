from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from .model_handler import ModelHandler
from .video_processor import VideoProcessor
from src.config import Config
from src.yolo.yolo_detector import YOLODetector
from src.detection.pose_detection import PoseDetector
from src.detection.face_detection import FaceDetector
from src.detection.siz_detection import SIZDetector
from .ui_components.model_selector import ModelSelector
from .ui_components.video_display import VideoDisplay
from .ui_components.control_panel import ControlPanel
import cv2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SIZ Tracking with YOLO")
        self.setGeometry(100, 100, 800, 600)
        
        # Инициализация детекторов
        self.yolo_detector = YOLODetector()
        self.pose_detector = PoseDetector()
        self.face_detector = FaceDetector()
        self.siz_detector = SIZDetector()
        self.cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        
        # Создаем центральный виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        
        # Инициализация компонентов UI
        self.video_display = VideoDisplay(self)
        self.model_selector = ModelSelector(self)
        self.control_panel = ControlPanel(self)
        
        # Добавляем компоненты в layout
        self.layout.addWidget(self.video_display)
        self.layout.addWidget(self.model_selector)
        self.layout.addWidget(self.control_panel)
        
        # Инициализация обработчиков
        self.model_handler = ModelHandler(self)
        self.video_processor = VideoProcessor(self)
        
        # Настройка соединений
        self._setup_connections()
        
        # Первоначальная загрузка
        self.model_selector.refresh_models(self.model_handler.refresh_models_list())
        
    def _setup_connections(self):
        """Настраивает все сигналы и слоты"""
        # Модели
        self.model_selector.model_selected.connect(self.model_handler.load_model)
        self.model_handler.model_loaded.connect(self.video_processor.on_model_loaded)
        
        # Управление видео
        self.control_panel.start_processing.connect(self.video_processor.start_processing)
        self.control_panel.stop_processing.connect(self.video_processor.stop_processing)
        self.control_panel.toggle_landmarks.connect(self.video_processor.toggle_landmarks)
        
        # Отображение видео
        self.video_processor.update_frame_signal.connect(self.video_display.update_frame)
        
    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)