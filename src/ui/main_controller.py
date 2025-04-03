from PyQt6.QtCore import QObject, pyqtSlot, QSettings, pyqtSignal
from .theme_manager import ThemeManager
from .model_manager import ModelManager
from .rtsp_manager import RtspManager
from .processing_manager import ProcessingManager
from utils.logger import AppLogger
from detection.yolo.yolo_detector import YOLODetector
from models.model_handler import ModelHandler
from .detection_controller import DetectionController
from .video_processor import VideoProcessor
from .ui_state_manager import UIStateManager

class MainController(QObject):
    theme_changed = pyqtSignal(bool)
    
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.logger = AppLogger.get_logger()
        self.settings = QSettings("MyCompany", "SIZDetector")
        self.processing_active = False
        
        # Инициализация подмодулей
        self.theme_manager = ThemeManager(self)
        self.model_manager = ModelManager(self)
        self.rtsp_manager = RtspManager(self)
        self.processing_manager = ProcessingManager(self)
        self.ui_state_manager = UIStateManager(self)  # Добавляем менеджер состояния UI
        
        self._init_components()
        self._setup_connections()
        
        # Загружаем данные при старте
        self.model_manager.refresh_models_list()  # Загрузка моделей
        self.rtsp_manager.load_rtsp_list()       # Загрузка RTSP списка
        self.theme_manager.load_theme_settings() # Загрузка темы
    
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
        # Подключение сигналов UI
        self.ui.start_btn.clicked.connect(self.processing_manager.on_start_stop)
        self.ui.landmarks_check.stateChanged.connect(self.video_processor.toggle_landmarks)
        self.ui.activate_model_btn.clicked.connect(self.model_manager.activate_model)
        self.ui.manage_models_btn.clicked.connect(self.model_manager.show_models_dialog)
        self.ui.source_type.currentIndexChanged.connect(self.processing_manager.update_source_type)
        self.ui.browse_btn.clicked.connect(self.processing_manager.handle_file_browse)
        self.ui.theme_btn.clicked.connect(self.theme_manager.toggle_theme)
        self.ui.add_rtsp_requested.connect(self.rtsp_manager.show_rtsp_dialog)

        # Обратные сигналы
        self.video_processor.update_frame.connect(self.ui.update_frame)
        self.video_processor.siz_status_changed.connect(self.processing_manager.update_siz_status)
        self.video_processor.input_error.connect(self.processing_manager.on_input_error)
        
        self.model_handler.model_loaded.connect(self.model_manager.on_model_loaded)
        self.model_handler.model_loading.connect(self.model_manager.on_model_loading)
        self.model_handler.models_updated.connect(self.model_manager.refresh_models_list)