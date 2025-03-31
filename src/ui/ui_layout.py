from PyQt6.QtWidgets import QVBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal
from .ui_components.control_panel import ControlPanel
from .ui_components.model_selector import ModelSelector
from .ui_components.video_display import VideoDisplay

class MainLayout(QWidget):
    start_processing = pyqtSignal()
    stop_processing = pyqtSignal()
    toggle_landmarks = pyqtSignal(bool)
    model_selected = pyqtSignal(str)
    load_model_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_handler = None
        self._init_ui()
        self._connect_signals()
        self.setProperty("class", "main-layout")

    def _init_ui(self):
        """Инициализация UI компонентов"""
        # Создаем дочерние виджеты с parent=self
        self.model_selector = ModelSelector(self)
        self.video_display = VideoDisplay(self)
        self.control_panel = ControlPanel(self)
        
        self.model_selector.setProperty("class", "model-selector")
        self.video_display.setProperty("class", "video-display")
        self.control_panel.setProperty("class", "control-panel")
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.video_display, stretch=3)
        layout.addWidget(self.model_selector, stretch=1)
        layout.addWidget(self.control_panel, stretch=1)
    
    def set_processing_state(self, active: bool):
        """Блокировка всех элементов управления"""
        self.control_panel.set_processing_state(active)
        self.model_selector.setEnabled(not active)
        
    def _connect_signals(self):
        """Подключение всех сигналов"""
        self.control_panel.start_processing.connect(self.start_processing)
        self.control_panel.stop_processing.connect(self.stop_processing)
        self.control_panel.toggle_landmarks.connect(self.toggle_landmarks)
        self.model_selector.model_selected.connect(self.model_selected)
        self.model_selector.load_model_requested.connect(self.load_model_requested)
    
    def refresh_models(self, models_list):
        """Публичный метод для обновления списка моделей"""
        self.model_selector.refresh_models(models_list)
    
    def set_model_handler(self, handler):
        """Устанавливает обработчик моделей"""
        self.model_handler = handler
        # Передаем в дочерние компоненты
        self.model_selector.set_model_handler(handler)  
        self.control_panel.set_model_handler(handler)
        