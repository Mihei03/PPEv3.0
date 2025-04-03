from PyQt6.QtCore import QObject, pyqtSlot, QSettings, pyqtSignal, Qt
from .theme_manager import ThemeManager
from ..models.model_manager import ModelManager
from ..models.rtsp_manager import RtspManager
from .processing_manager import ProcessingManager
from core.utils.logger import AppLogger
from core.detection.yolo_detector import YOLODetector
from models.model_handler import ModelHandler
from .detection_controller import DetectionController
from ..processing.video_processor import VideoProcessor
from .ui_state_manager import UIStateManager
from ...ui.builders.ui_builder import UIBuilder
import os

class MainController(QObject):
    theme_changed = pyqtSignal(bool)
    
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.logger = AppLogger.get_logger()
        self.settings = QSettings("MyCompany", "SIZDetector")
        self.processing_active = False
        
        # 1. Сначала инициализируем UI
        self.ui.ui_builder = UIBuilder(self.ui)
        self.ui.ui_builder.build_ui()

        if not hasattr(self.ui, 'control_panel'):
            from ui.components.control_panel import ControlPanel
            self.ui.control_panel = ControlPanel(self.ui)

        # Делаем компоненты доступными
        self.ui.video_display = self.ui.ui_builder.video_display
        self.ui.model_panel = self.ui.ui_builder.model_panel
        self.ui.control_panel = self.ui.ui_builder.control_panel
        self.ui.status_bar = self.ui.ui_builder.status_bar
    
        # 2. Затем создаем подмодули
        self.theme_manager = ThemeManager(self)
        self.model_manager = ModelManager(self)
        self.rtsp_manager = RtspManager(self) 
        self.processing_manager = ProcessingManager(self)
        self.ui_state_manager = UIStateManager(self)
        
        # 3. Инициализируем компоненты
        self._init_components()
        
        # 4. Настраиваем соединения
        self._setup_connections()
        
        # 5. Загружаем данные (после полной инициализации)
        self.model_manager.refresh_models_list()
        self.rtsp_manager.load_rtsp_list()  # Теперь UI точно готов
        self.theme_manager.load_theme_settings()
        self.ui.destroyed.connect(self.cleanup)

    def _init_components(self):
        self.yolo_detector = YOLODetector()
        self.model_handler = ModelHandler()
        self.model_handler.set_yolo_detector(self.yolo_detector)
        
        self.detection_controller = DetectionController()
        self.detection_controller.setup_detectors()
        self.detection_controller.yolo = self.yolo_detector
        
        self.video_processor = VideoProcessor()
        self.video_processor.set_detectors(
            self.yolo_detector,
            self.detection_controller.face,
            self.detection_controller.pose,
            self.detection_controller.siz
        )

    def _setup_connections(self):
        # Подключение сигналов UI через control_panel
        self.ui.control_panel.start_btn.clicked.connect(
            self.processing_manager.on_start_stop
        )
        self.ui.model_panel.model_combo.currentTextChanged.connect(
            self._handle_model_changed
        )
        self.video_processor.processing_stopped.connect(
            lambda: self.processing_manager.set_processing_state(False)
        )
        self.ui.control_panel.source_input.textChanged.connect(
            self._validate_source_input
        )
        self.ui.ui_builder.control_panel.landmarks_check.stateChanged.connect(
            lambda state: self.video_processor.toggle_landmarks(state == Qt.CheckState.Checked.value)
        )
        self.ui.model_panel.activate_model_btn.clicked.connect(
            self.model_manager.activate_model
        )
        self.ui.model_panel.manage_models_btn.clicked.connect(
            self.model_manager.show_models_dialog
        )
        self.ui.ui_builder.control_panel.source_type.currentIndexChanged.connect(
            self.processing_manager.update_source_type
        )
        self.ui.ui_builder.control_panel.browse_btn.clicked.connect(self.processing_manager.handle_file_browse)
        self.ui.ui_builder.status_bar.theme_btn.clicked.connect(self.theme_manager.toggle_theme)
        self.ui.ui_builder.control_panel.add_rtsp_btn.clicked.connect(self.rtsp_manager.show_rtsp_dialog)

        # Обратные сигналы
        self.video_processor.update_frame.connect(self.ui.ui_builder.video_display.update_frame)
        self.video_processor.siz_status_changed.connect(self.processing_manager.update_siz_status)
        self.video_processor.input_error.connect(self.processing_manager.on_input_error)
        
        self.model_handler.model_loaded.connect(self.model_manager.on_model_loaded)
        self.model_handler.model_loading.connect(self.model_manager.on_model_loading)
        self.model_handler.models_updated.connect(self.model_manager.refresh_models_list)
    
    def _handle_model_changed(self):
        """Дополнительная обработка изменения модели"""
        self.ui.control_panel.start_btn.setEnabled(False)
        self.ui.status_bar.show_message("Выбрана новая модель - требуется активация", 2000)

    def cleanup(self):
        """Освобождение ресурсов при закрытии"""
        if hasattr(self, 'video_processor'):
            self.video_processor.stop_processing()
        if hasattr(self, 'input_handler') and self.input_handler.cap:
            self.input_handler.release()
        self.logger.info("Приложение завершает работу, ресурсы освобождены")

    def _validate_source_input(self):
        source_type = self.ui.control_panel.source_type.currentIndex()
        source = self.ui.control_panel.source_input.text()
        
        if source_type == 0:  # Камера
            try:
                camera_idx = int(source)
                valid = camera_idx >= 0
            except ValueError:
                valid = False
        elif source_type == 1:  # Файл
            valid = os.path.exists(source)
        else:  # RTSP
            valid = source.startswith('rtsp://')
        
        self.ui.control_panel.start_btn.setEnabled(
            valid and self.model_handler.is_model_activated()
        )