from PyQt6.QtCore import pyqtSignal
from ..components.video_display import VideoDisplay
from ..components.model_panel import ModelPanel
from ..components.control_panel import ControlPanel
from ..components.status_bar import StatusBar

class UIBuilder:
    def __init__(self, main_window):
        self.main_window = main_window
        self.video_display = None
        self.model_panel = None
        self.control_panel = None
        self.status_bar = None
        self._init_signals()
        
    def _init_signals(self):
        # Сигналы UI
        self.main_window.start_processing = pyqtSignal()
        self.main_window.stop_processing = pyqtSignal()
        self.main_window.toggle_landmarks = pyqtSignal(bool)
        self.main_window.model_selected = pyqtSignal(str)
        self.main_window.load_model_requested = pyqtSignal()
        self.main_window.video_source_changed = pyqtSignal(str, int)
        self.main_window.rtsp_selected = pyqtSignal(str)
        self.main_window.add_rtsp_requested = pyqtSignal()
        self.main_window.manage_models_requested = pyqtSignal()

    def build_ui(self):
        self.main_window.setWindowTitle("Система обнаружения СИЗ")
        
        # Создаем компоненты
        self.video_display = VideoDisplay(self.main_window)
        self.model_panel = ModelPanel(self.main_window)
        self.control_panel = ControlPanel(self.main_window)
        self.status_bar = StatusBar(self.main_window)
        self.model_panel.model_combo.currentTextChanged.connect(
            lambda: self.control_panel.start_btn.setEnabled(False)
        )
        self.main_window.model_panel = self.model_panel
        self.main_window.control_panel = self.control_panel
        # Собираем основной layout
        from PyQt6.QtWidgets import QVBoxLayout, QWidget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        main_layout.addWidget(self.video_display.scroll_area, stretch=1)
        main_layout.addWidget(self.model_panel.panel)
        main_layout.addWidget(self.control_panel.panel)
        
        self.main_window.setCentralWidget(central_widget)
        self.main_window.setStatusBar(self.status_bar.bar)
        # Инициализация
        self.control_panel._update_source_type(0)