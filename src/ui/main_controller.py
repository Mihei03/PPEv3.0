from PyQt6.QtCore import QObject, pyqtSlot, QSettings, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QApplication, QWidget
from ui.ui_components.rtsp_storage import RtspStorage
from ui.ui_components.rtsp_manager import RtspManagerDialog
import os
from .model_handler import ModelHandler
from .video_processor import VideoProcessor
from .detection_controller import DetectionController
from utils.logger import AppLogger
from ui.ui_components.rtsp_storage import RtspStorage
from yolo.yolo_detector import YOLODetector

class MainController(QObject):
    theme_changed = pyqtSignal(bool)
    
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.logger = AppLogger.get_logger()
        self.settings = QSettings("MyCompany", "SIZDetector")
        self._dark_mode = self.settings.value("dark_mode", False, type=bool)
        self.current_model = None
        self.current_siz_status = None
        self.processing_active = False
        
        self._init_components()
        self._load_initial_state()
        self._setup_connections()

    def _init_components(self):
        
        # 1. Сначала создаем YOLO детектор
        self.yolo_detector = YOLODetector()
        self.logger.info("YOLO детектор создан")
        
        # 2. Инициализируем ModelHandler
        self.model_handler = ModelHandler()
        self.model_handler.set_yolo_detector(self.yolo_detector)
        self.logger.info("ModelHandler инициализирован с YOLO детектором")
        
        # 3. Инициализируем DetectionController
        self.detection_controller = DetectionController()
        self.detection_controller.yolo = self.yolo_detector
        self.logger.info("DetectionController инициализирован")
        
        # 4. Инициализируем VideoProcessor
        self.video_processor = VideoProcessor()
        self.video_processor.set_detectors(
            self.yolo_detector,
            self.detection_controller.face,
            self.detection_controller.pose,
            self.detection_controller.siz
        )
        self.logger.info("VideoProcessor инициализирован с детекторами")

    def _setup_connections(self):
        # UI сигналы
        self.ui.start_btn.clicked.connect(self._on_start_stop)
        self.ui.landmarks_check.stateChanged.connect(
            lambda state: self.video_processor.toggle_landmarks(state == 2)  # Qt.Checked = 2
        )
        self.ui.model_combo.currentTextChanged.connect(self._on_model_selected)
        self.ui.add_model_btn.clicked.connect(self._load_new_model)
        self.ui.source_type.currentIndexChanged.connect(self._update_source_type)
        self.ui.browse_btn.clicked.connect(self._handle_file_browse)
        self.ui.theme_btn.clicked.connect(self._toggle_theme)
        self.ui.add_rtsp_requested.connect(self._show_rtsp_dialog)

        # Обратные сигналы
        self.video_processor.update_frame.connect(self.ui.video_display.setPixmap)
        self.video_processor.siz_status_changed.connect(self._update_siz_status)
        self.video_processor.input_error.connect(self._on_input_error)
        
        self.model_handler.model_loaded.connect(self._on_model_loaded)
        self.model_handler.model_loading.connect(self._on_model_loading)
        self.model_handler.models_updated.connect(self._refresh_models_list)

    def _load_initial_state(self):
        self._load_theme_settings()
        self._load_initial_models()
        self._update_source_type(0)  # Инициализация типа источника
        self._load_rtsp_list()      # Загрузка RTSP списка
        self.ui.show_message("Выберите модель и нажмите Start")

    def _load_rtsp_list(self):
        """Загружает и обновляет список RTSP потоков"""
        try:
            from ui.ui_components.rtsp_storage import RtspStorage
            rtsp_storage = RtspStorage()
            rtsp_list = rtsp_storage.get_all_rtsp()
            
            current_selection = self.ui.rtsp_combo.currentText()
            self.ui.rtsp_combo.clear()
            
            if rtsp_list:
                self.ui.rtsp_combo.addItems(sorted(rtsp_list.keys()))
                self.ui.rtsp_combo.setEnabled(True)
                
                # Восстанавливаем предыдущий выбор, если он существует
                if current_selection in rtsp_list:
                    self.ui.rtsp_combo.setCurrentText(current_selection)
            else:
                self.ui.rtsp_combo.addItem("Нет сохраненных RTSP")
                self.ui.rtsp_combo.setEnabled(False)
                
        except Exception as e:
            self.logger.error(f"Ошибка загрузки RTSP: {str(e)}")
            self.ui.rtsp_combo.clear()
            self.ui.rtsp_combo.addItem("Ошибка загрузки")


    @pyqtSlot()
    def _on_start_stop(self):
        if self.processing_active:
            self._on_stop_processing()
        else:
            self._on_start_processing()

    @pyqtSlot()
    def _on_start_processing(self):
        if not self.current_model:
            self.ui.show_message("Сначала выберите модель!", 3000)
            return
            
        if not self.model_handler.is_model_activated():
            self.ui.show_message("Модель не активирована!", 3000)
            return
            
        source_type = self.ui.source_type.currentIndex()
        source = self.ui.source_input.text().strip()
        
        if source_type == 2:  # RTSP
            rtsp_data = self._get_current_rtsp()
            if not rtsp_data or not rtsp_data.get("url"):
                self.ui.show_warning("Ошибка", "Выберите RTSP поток")
                return
            source = rtsp_data["url"]
        
        if not source:
            self.ui.show_warning("Ошибка", "Введите источник видео")
            return
        
        if self.video_processor.set_video_source(source, source_type):
            self.processing_active = True
            self._set_processing_state(True)
            self.video_processor.start_processing()
            self.ui.show_message("Обработка запущена", 3000)
        else:
            self.ui.show_message("Ошибка инициализации источника", 3000)

    def _get_current_rtsp_url(self):
        current_name = self.ui.rtsp_combo.currentText()
        if current_name and current_name != "Нет сохраненных RTSP":
            rtsp_storage = RtspStorage()
            rtsp_data = rtsp_storage.get_all_rtsp().get(current_name, {})
            return rtsp_data.get("url", "")
        return ""
    
    def _update_source_type(self, index):
        placeholders = [
            "Введите индекс камеры (0, 1, ...)",
            "Введите путь к видеофайлу",
            "Выберите RTSP поток"
        ]
        self.ui.source_input.setPlaceholderText(placeholders[index])
        self.ui.source_input.clear()
        
        is_file = index == 1
        is_rtsp = index == 2
        
        self.ui.browse_btn.setVisible(is_file)
        self.ui.rtsp_combo.setVisible(is_rtsp)
        self.ui.add_rtsp_btn.setVisible(is_rtsp)
        self.ui.source_input.setVisible(not is_rtsp)
        
        if index == 0:  # Камера
            self.ui.source_input.setText("0")

    def _handle_file_browse(self):
        """Обработка выбора файла с бизнес-логикой"""
        if self.ui.source_type.currentIndex() == 1:  # Видеофайл
            # Используем существующий текст как начальную директорию
            initial_dir = os.path.dirname(self.ui.source_input.text()) if self.ui.source_input.text() else ""
            
            file_path, _ = QFileDialog.getOpenFileName(
                self.ui,
                "Выберите видеофайл",
                initial_dir,
                "Video Files (*.mp4 *.avi *.mov *.mkv)"
            )
            
            if file_path:
                self.ui.source_input.setText(file_path)
                # Дополнительная бизнес-логика при необходимости
                self._on_video_source_changed(file_path, 1)  # 1 - тип "Видеофайл"

    @pyqtSlot()
    def _on_stop_processing(self):
        self.processing_active = False
        self._set_processing_state(False)
        self.video_processor.stop_processing()
        
        status_message = f"Обработка остановлена | Модель: {self.current_model}"
        if self.current_siz_status is not None:
            status_message += f" | Статус СИЗ: {'OK' if self.current_siz_status else 'Ошибка'}"
        self.ui.show_message(status_message)

    def _set_processing_state(self, active):
        widgets = [
            self.ui.source_type,
            self.ui.source_input,
            self.ui.browse_btn,
            self.ui.rtsp_combo,
            self.ui.add_rtsp_btn,
            self.ui.landmarks_check,
            self.ui.model_combo,
            self.ui.activate_model_btn,
            self.ui.add_model_btn
        ]
        
        for widget in widgets:
            widget.setEnabled(not active)
        
        self.ui.start_btn.setText("Stop" if active else "Start")
        self.ui.start_btn.setEnabled(True)

    @pyqtSlot(str)
    def _on_model_selected(self, model_name):
        """Обработчик только для активации по кнопке"""
        if not model_name or model_name == "Нет доступных моделей":
            self.ui.show_message("Не выбрана модель", 3000)
            return
            
        self.logger.info(f"Начало активации модели: {model_name}")
        
        # Блокируем интерфейс на время загрузки
        self._set_ui_enabled(False)
        
        try:
            if self.model_handler.load_model(model_name):
                self.current_model = model_name
                self.ui.show_message(f"Модель '{model_name}' активирована", 3000)
                self.ui.start_btn.setEnabled(True)
            else:
                self.ui.show_message(f"Ошибка активации модели", 3000)
        finally:
            self._set_ui_enabled(True)

    def _set_ui_enabled(self, enabled):
        """Блокировка/разблокировка интерфейса"""
        widgets = [
            self.ui.model_combo,
            self.ui.activate_model_btn,
            self.ui.add_model_btn,
            self.ui.start_btn
        ]
        for widget in widgets:
            widget.setEnabled(enabled)

    def _load_model(self, model_name):
        self.logger.info(f"Активация модели: {model_name}")
        self.ui.show_message(f"Активация модели {model_name}...", 3000)
        
        if self.model_handler.load_model(model_name):
            self.current_model = model_name
            self.ui.show_message(f"Модель '{model_name}' активирована", 3000)
            self.ui.start_btn.setEnabled(True)
        else:
            self.ui.show_message(f"Ошибка активации модели", 3000)
            self.ui.start_btn.setEnabled(False)

    @pyqtSlot(str, dict)
    def _on_model_loaded(self, model_name, model_info):
        if self.video_processor.load_model(model_name, model_info):
            self.current_model = model_name
            self.ui.start_btn.setEnabled(True)
            self.ui.show_message(f"Модель '{model_name}' готова", 3000)
        else:
            self.ui.start_btn.setEnabled(False)
            self.ui.show_message(f"Ошибка инициализации модели '{model_name}'", 3000)

    @pyqtSlot(str, int)
    def _on_video_source_changed(self, source, source_type):
        success = self.video_processor.set_video_source(source, source_type)
        self.ui.start_btn.setEnabled(success and bool(self.current_model))
        
        if success:
            self.ui.show_message(f"Источник готов: {source}", 3000)
        else:
            self.ui.show_message("Ошибка источника - исправьте ввод", 3000)

    @pyqtSlot(str)
    def _on_input_error(self, error_msg):
        self.ui.show_warning("Ошибка источника", error_msg)
        self.ui.show_message(error_msg, 5000)
        self.ui.start_btn.setEnabled(False)

    @pyqtSlot(object)
    def _update_siz_status(self, status):
        try:
            if status == "nothing":
                message = "СИЗ: ничего не обнаружено!"
            elif isinstance(status, list):
                message = "СИЗ: все на местах" if all(status) else "СИЗ: обнаружены не все!"
            else:
                message = "СИЗ: все на местах" if status else "СИЗ: проблемы обнаружены!"
            
            base_msg = f"Модель: {self.current_model} | " if self.current_model else ""
            self.ui.show_message(base_msg + message)
            self.current_siz_status = all(status) if isinstance(status, list) else status
            
        except Exception as e:
            self.logger.error(f"Status update error: {str(e)}")
            self.ui.show_message("Ошибка обновления статуса")

    @pyqtSlot()
    def _load_new_model(self):
        if self.model_handler.add_model_from_folder():
            models = self.model_handler.refresh_models_list()
            self._refresh_models_list()
            self.ui.show_message("Модель успешно добавлена", 3000)

    @pyqtSlot()
    def _refresh_models_list(self):
        models = self.model_handler.refresh_models_list()
        self.ui.model_combo.clear()
        
        if models:
            self.ui.model_combo.addItems(models)
            self.ui.show_message(f"Доступно моделей: {len(models)}", 3000)
        else:
            self.ui.model_combo.addItem("Нет доступных моделей")
            self.ui.show_message("Модели не найдены! Добавьте модель через меню", 3000)
            self.ui.start_btn.setEnabled(False)

    @pyqtSlot(str)
    def _on_model_loading(self, model_name):
        self.ui.show_message(f"Загрузка модели {model_name}...")

    @pyqtSlot(str)
    def _on_rtsp_selected(self, name):
        if name:
            rtsp_data = self._get_current_rtsp()
            if rtsp_data and rtsp_data.get("url"):
                self.ui.source_input.setText(rtsp_data["url"])
                self.ui.source_type.setCurrentIndex(2)

    def _get_current_rtsp(self):
        """Получает данные текущего выбранного RTSP потока"""
        current_name = self.ui.rtsp_combo.currentText()
        if current_name:
            # Используем rtsp_storage из control_panel (если он там есть)
            if hasattr(self.ui, 'control_panel') and hasattr(self.ui.control_panel, 'rtsp_storage'):
                return self.ui.control_panel.rtsp_storage.get_all_rtsp().get(current_name, {})
            
            # Альтернативный вариант - создаем временное хранилище
            rtsp_storage = RtspStorage()
            return rtsp_storage.get_all_rtsp().get(current_name, {})
        return {}

    def _show_rtsp_dialog(self):
        try:      
            rtsp_storage = RtspStorage()
            dialog = RtspManagerDialog(rtsp_storage, self.ui)
            
            # Подключаем сигнал об изменениях
            dialog.data_changed.connect(self._load_rtsp_list)
            
            dialog.exec()
                
        except Exception as e:
            self.logger.error(f"Ошибка открытия диалога RTSP: {str(e)}")
            self.ui.show_warning("Ошибка", "Не удалось открыть диалог управления RTSP")


    def _load_initial_models(self):
        models = self.model_handler.refresh_models_list()
        self._refresh_models_list()

    @pyqtSlot()
    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self.settings.setValue("dark_mode", self._dark_mode)
        self._update_theme_button()
        self._apply_theme(self._dark_mode)
        self.theme_changed.emit(self._dark_mode)

    def _apply_theme(self, dark_mode):
        """Применение темы через установку класса для всего приложения"""
        try:
            app = QApplication.instance()
            
            # Устанавливаем или удаляем класс dark-mode для главного окна
            if dark_mode:
                self.ui.setProperty("class", "dark-mode")
            else:
                self.ui.setProperty("class", "")
                
            # Обновляем стили всех виджетов
            self._update_styles()
            
        except Exception as e:
            self.logger.error(f"Ошибка применения темы: {str(e)}")

    def _update_styles(self):
        """Обновление стилей всех виджетов"""
        for widget in [self.ui] + self.ui.findChildren(QWidget):
            try:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
            except:
                continue

    def _update_theme_button(self):
        self.ui.theme_btn.setText("☀️" if self._dark_mode else "🌙")

    def _load_theme_settings(self):
        """Загружает сохраненные настройки темы"""
        self._dark_mode = self.settings.value("dark_mode", False, type=bool)
        self._update_theme_button()
        self._apply_theme(self._dark_mode)
        self.theme_changed.emit(self._dark_mode)