from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal
from .ui_components.model_selector import ModelSelector
from .ui_components.video_display import VideoDisplay
from .ui_components.control_panel import ControlPanel

class MainLayout(QWidget):
    start_processing = pyqtSignal()
    stop_processing = pyqtSignal()
    toggle_landmarks = pyqtSignal(bool)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.model_selector = ModelSelector(parent)
        self.video_display = VideoDisplay(parent)
        self.control_panel = ControlPanel(parent)
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.video_display)
        layout.addWidget(self.model_selector)
        layout.addWidget(self.control_panel)
        self.setLayout(layout)
        
        # Соединение сигналов
        self.control_panel.start_processing.connect(self.start_processing)
        self.control_panel.stop_processing.connect(self.stop_processing)
        self.control_panel.toggle_landmarks.connect(self.toggle_landmarks)