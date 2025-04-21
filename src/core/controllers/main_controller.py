from PyQt6.QtCore import QObject, pyqtSlot, QSettings, pyqtSignal, Qt

from core.processing.input_handler import InputHandler
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
from rtsp.rtsp_manager import RtspManagerDialog  # Добавленный импорт
from rtsp.rtsp_storage import RtspStorage  # Добавленный импорт
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

        self.input_handler = InputHandler()

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
        self.rtsp_storage = RtspStorage()  # Создаем хранилище RTSP
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
        self.rtsp_manager.load_rtsp_list()
        self.theme_manager.load_theme_settings()
        self.ui.destroyed.connect(self.cleanup)
        self.rtsp_manager.load_rtsp_list()

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
        self.ui.control_panel.rtsp_combo.currentTextChanged.connect(
            self._handle_rtsp_selection
        )
        self.ui.ui_builder.control_panel.landmarks_check.stateChanged.connect(
            lambda state: self.video_processor.toggle_landmarks(state == Qt.CheckState.Checked.value)
        )
        self.ui.model_panel.activate_model_btn.clicked.connect(
            self.model_manager.activate_model
        )
        self.ui.control_panel.manage_models_btn.clicked.connect(
            self.model_manager.show_models_dialog
        )
        self.ui.control_panel.source_type.currentIndexChanged.connect(
            self._handle_source_type_change
        )
        self.ui.ui_builder.control_panel.source_type.currentIndexChanged.connect(
            self.processing_manager.update_source_type
        )
        self.ui.ui_builder.control_panel.browse_btn.clicked.connect(self.processing_manager.handle_file_browse)
        self.ui.ui_builder.status_bar.theme_btn.clicked.connect(self._toggle_theme)
        self.ui.ui_builder.control_panel.add_rtsp_btn.clicked.connect(self._show_rtsp_dialog)

        # Обратные сигналы
        self.video_processor.update_frame.connect(self.ui.ui_builder.video_display.update_frame)
        self.video_processor.siz_status_changed.connect(self.processing_manager.update_siz_status)
        self.video_processor.input_error.connect(self.processing_manager.on_input_error)
        
        self.model_handler.model_loaded.connect(self.model_manager.on_model_loaded)
        self.model_handler.model_loading.connect(self.model_manager.on_model_loading)
        self.model_handler.models_updated.connect(self.model_manager.refresh_models_list)
        
        # Подключение сигнала изменения темы
        self.theme_changed.connect(self.theme_manager.apply_theme)

    def _handle_source_type_change(self, index):
        """Обрабатывает изменение типа источника видео"""
        if index == 2:  # RTSP
            # Загружаем актуальный список RTSP
            self.rtsp_manager.load_rtsp_list()
            # Проверяем текущий выбор
            self.rtsp_manager.validate_rtsp_selection()
        else:
            # Для других источников используем стандартную валидацию
            self.ui.control_panel._validate_current_input(
                self.ui.control_panel.source_input.text()
            )

    def _handle_rtsp_selection(self):
        """Обработчик изменения выбора RTSP потока"""
        if self.ui.control_panel.source_type.currentIndex() == 2:  # Если выбран RTSP
            self.rtsp_manager.validate_rtsp_selection()
            
    def _toggle_theme(self):
        """Обработчик переключения темы"""
        # Получаем текущее состояние темы
        current_theme = self.theme_manager.is_dark_theme()
        # Инвертируем его для переключения
        self.theme_manager.toggle_theme()
        # Испускаем сигнал с новым состоянием темы
        self.theme_changed.emit(not current_theme)

    def _show_rtsp_dialog(self):
        """Показывает диалог управления RTSP потоками с передачей model_handler"""
        dialog = RtspManagerDialog(
            rtsp_storage=self.rtsp_storage,
            model_handler=self.model_handler,
            parent=self.ui  # Передаем главное окно как родителя
        )
        dialog.data_changed.connect(self.rtsp_manager.load_rtsp_list)
        dialog.exec()
    
    def _handle_model_changed(self):
        """Дополнительная обработка изменения модели"""
        self.ui.control_panel.start_btn.setEnabled(False)
        self.ui.status_bar.show_message("Выбрана новая модель - требуется активация", 2000)

    def cleanup(self):
        """Освобождение ресурсов при закрытии"""
        try:
            if hasattr(self, 'video_processor'):
                self.video_processor.cleanup()
            if hasattr(self, 'input_handler') and self.input_handler.cap:
                self.input_handler.release()
            self.logger.info("Приложение завершает работу, ресурсы освобождены")
        except Exception as e:
            self.logger.error(f"Ошибка при очистке ресурсов: {str(e)}")

    def _validate_source_input(self):
        source_type = self.ui.control_panel.source_type.currentIndex()
        source = self.ui.control_panel.source_input.text().strip()
        
        # Базовая проверка заполненности поля
        if source_type == 0:  # Камера
            try:
                camera_idx = int(source)
                field_valid = camera_idx >= 0
            except ValueError:
                field_valid = False
        elif source_type == 1:  # Для файла
            field_valid = bool(source) and source != "0"
        else:  # RTSP
            field_valid = bool(source)
        
        model_activated = bool(self.model_handler.is_model_activated())
        self.ui.control_panel.start_btn.setEnabled(field_valid and model_activated)