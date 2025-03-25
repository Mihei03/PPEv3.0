from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal
from .ui_components.model_selector import ModelSelector
from .ui_components.video_display import VideoDisplay
from .ui_components.control_panel import ControlPanel

class MainLayout(QWidget):
    start_processing = pyqtSignal()
    stop_processing = pyqtSignal()
    toggle_landmarks = pyqtSignal(bool)
    model_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._connect_signals()
        
    def _init_ui(self):
        """Инициализация UI компонентов"""
        # Создаем дочерние виджеты с parent=self
        self.model_selector = ModelSelector(self)
        self.video_display = VideoDisplay(self)
        self.control_panel = ControlPanel(self)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.video_display, stretch=3)
        layout.addWidget(self.model_selector, stretch=1)
        layout.addWidget(self.control_panel, stretch=1)
        
    def _connect_signals(self):
        """Подключение всех сигналов"""
        self.control_panel.start_processing.connect(self.start_processing)
        self.control_panel.stop_processing.connect(self.stop_processing)
        self.control_panel.toggle_landmarks.connect(self.toggle_landmarks)
        self.model_selector.model_selected.connect(self.model_selected)
    
    def refresh_models(self, models_list):
        """Публичный метод для обновления списка моделей"""
        self.model_selector.refresh_models(models_list)