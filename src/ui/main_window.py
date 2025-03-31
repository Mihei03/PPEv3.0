from PyQt6.QtWidgets import QMainWindow, QMessageBox, QPushButton, QWidget
from PyQt6.QtCore import pyqtSlot, QSettings, Qt
from .model_handler import ModelHandler
from .video_processor import VideoProcessor
from src.yolo.yolo_detector import YOLODetector
from src.detection.face_detection import FaceDetector
from src.detection.pose_detection import PoseDetector
from src.detection.siz_detection import SIZDetector
from .ui_layout import MainLayout
from utils.logger import AppLogger
from PyQt6.QtCore import QSettings

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._settings = QSettings("MyCompany", "SIZDetector")
        self._dark_mode = False
        self.logger = AppLogger.get_logger()
        
        # Инициализируем основные компоненты
        self.model_handler = ModelHandler(self)
        self._init_ui()  # Сначала UI
        self._init_detectors()
        self._setup_connections()
        self._init_status_vars()
        self._load_initial_models()
        
        # Применяем тему в конце
        self._load_theme_settings()

    def _load_theme_settings(self):
        """Загружает настройки темы и применяет их"""
        self._dark_mode = self._settings.value("dark_mode", False, type=bool)
        self._apply_theme(self._dark_mode)
        self._update_theme_button()

    def _update_theme_button(self):
        """Обновляет иконку кнопки темы"""
        self._theme_btn.setText("☀️" if self._dark_mode else "🌙")

    def _init_status_vars(self):
        """Инициализация переменных статуса"""
        self.current_model = None
        self.current_siz_status = None
        self.processing_active = False
        self.statusBar().showMessage("Выберите модель и нажмите Start")

    def _init_ui(self):
        self.setWindowTitle("Система обнаружения СИЗ")
        self.setGeometry(100, 100, 800, 600)
        
        # Сначала создаем main_layout
        self.main_layout = MainLayout(self)
        self.setCentralWidget(self.main_layout)
        
        # Затем устанавливаем model_handler
        self.main_layout.set_model_handler(self.model_handler)
        
        # Кнопка темы
        self._theme_btn = QPushButton()
        self._theme_btn.setProperty("class", "theme-toggle")
        self._theme_btn.clicked.connect(self._toggle_theme)
        self.statusBar().addPermanentWidget(self._theme_btn)

    def _init_detectors(self):
        self.yolo = YOLODetector()
        self.pose = PoseDetector()
        self.face = FaceDetector()
        self.siz = SIZDetector()
        
        self.video_processor = VideoProcessor()
        self.video_processor.set_detectors(self.yolo, self.face, self.pose, self.siz)
        
        self.model_handler = ModelHandler(self)

    def _update_theme_btn_icon(self):
        """Обновляет иконку кнопки в соответствии с текущей темой"""
        self.theme_btn.setText("☀️" if self.dark_mode else "🌙")

    def _toggle_theme(self):
        """Переключает тему на противоположную"""
        self._dark_mode = not self._dark_mode
        self._settings.setValue("dark_mode", self._dark_mode)
        self._apply_theme(self._dark_mode)
        self._update_theme_button()

    def _apply_theme(self, dark_mode):
        """Применяет тему через CSS"""
        theme_class = "dark-mode" if dark_mode else ""
        self.setProperty("class", theme_class)
        
        # Обновляем стиль для всех виджетов
        for widget in [self] + self.findChildren(QWidget):
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def _setup_connections(self):
        """Настройка всех соединений"""
        if not hasattr(self, 'main_layout'):
            self.logger.error("MainLayout not initialized!")
            return
        # Подключение сигналов от layout
        self.main_layout.start_processing.connect(self._on_start_processing)
        self.main_layout.stop_processing.connect(self._on_stop_processing)
        self.main_layout.toggle_landmarks.connect(
            lambda state: self.video_processor.toggle_landmarks(state))
        self.main_layout.model_selected.connect(self._on_model_selected)
        self.main_layout.load_model_requested.connect(self._load_new_model)

        # Подключение сигналов от ModelHandler (ИСПРАВЛЕНО)
        self.model_handler.model_loaded.connect(self._on_model_loaded)  # Только один слот
        self.model_handler.model_loading.connect(self._on_model_loading)
        self.model_handler.models_updated.connect(self._refresh_models_list)
        
        # Подключение сигналов к layout
        self.video_processor.update_frame_signal.connect(
            self.main_layout.video_display.update_frame
        )
        self.video_processor.siz_status_changed.connect(
            self._update_siz_status
        )

        # Подключения для управления источником видео
        self.main_layout.control_panel.video_source_changed.connect(
            self._on_video_source_changed
        )
        self.video_processor.input_error.connect(
            self._on_input_error
        )
    
    @pyqtSlot()
    def _load_new_model(self):
        """Обработчик добавления новой модели"""
        if self.model_handler.add_model_from_folder():
            models = self.model_handler.refresh_models_list()
            self.main_layout.refresh_models(models)
            self.statusBar().showMessage("Модель успешно добавлена", 3000)

    @pyqtSlot(str, int)
    def _on_video_source_changed(self, source: str, source_type: int):
        """Обработчик изменения источника с управлением кнопкой"""
        if self.main_layout.control_panel.source_type.currentIndex() == 2:  # RTSP поток
            rtsp_data = self.main_layout.control_panel.get_current_rtsp()
            if rtsp_data:
                url = rtsp_data.get("url", "")
            if not source:
                self.main_layout.control_panel.set_start_button_enabled(False)
                return
            
        success = self.video_processor.set_video_source(source, source_type)
        self.main_layout.control_panel.set_start_button_enabled(success)
        
        if success:
            self.statusBar().showMessage(f"Источник готов: {source}", 3000)
        else:
            self.statusBar().showMessage("Ошибка источника - исправьте ввод", 3000)
            
    @pyqtSlot(str)
    def _on_input_error(self, error_msg):
        """Улучшенные сообщения об ошибках"""
        QMessageBox.warning(self, "Ошибка источника", error_msg)
        self.statusBar().showMessage(error_msg, 5000)
        self.main_layout.control_panel.set_start_button_enabled(False)

    @pyqtSlot(bool)
    def _enable_start_button(self, enabled):
        """Активирует/деактивирует кнопку Start"""
        self.main_layout.control_panel.set_start_button_enabled(enabled and self.current_model is not None)
           
    @pyqtSlot()
    def _on_start_processing(self):
        """Запуск обработки"""
        if not self.current_model:
            self.statusBar().showMessage("Сначала выберите модель!", 3000)
            return
            
        self.processing_active = True
        self.main_layout.set_processing_state(True)  # Блокируем элементы
        self.video_processor.start_processing()
        self.statusBar().showMessage("Обработка запущена", 3000)

    @pyqtSlot()
    def _on_stop_processing(self):
        """Остановка обработки"""
        self.processing_active = False
        self.main_layout.set_processing_state(False)  # Разблокируем элементы
        self.video_processor.stop_processing()
        
        status_message = f"Обработка остановлена | Модель: {self.current_model}"
        if self.current_siz_status is not None:
            status_message += f" | Статус СИЗ: {'OK' if self.current_siz_status else 'Ошибка'}"
        self.statusBar().showMessage(status_message)

    @pyqtSlot()
    def _refresh_models_list(self):
        """Обновляет список моделей в интерфейсе"""
        try:
            # Получаем обновленный список моделей
            models = self.model_handler.refresh_models_list()
            
            # Обновляем выпадающий список в интерфейсе
            self.main_layout.model_selector.refresh_models(models)
            
            # Обновляем статус в статус-баре
            if models:
                self.statusBar().showMessage(f"Доступно моделей: {len(models)}", 3000)
            else:
                self.statusBar().showMessage("Модели не найдены! Добавьте модель через меню", 3000)
                self.main_layout.control_panel.set_start_button_enabled(False)
                
        except Exception as e:
            self.logger.error(f"Ошибка обновления списка моделей: {str(e)}")
            self.statusBar().showMessage("Ошибка загрузки списка моделей", 3000)

    @pyqtSlot(str)
    def _on_model_loading(self, model_name: str):
        """Обновление статуса при загрузке модели"""
        self.statusBar().showMessage(f"Загрузка модели {model_name}...")

    @pyqtSlot(str, dict)
    def _on_model_loaded(self, model_name: str, model_info: dict):
        """Обработка загрузки модели"""
        if self.video_processor.load_model(model_name, model_info):
            self.current_model = model_name
            self.main_layout.control_panel.set_start_button_enabled(True)
            self.statusBar().showMessage(f"Модель '{model_name}' готова", 3000)
        else:
            self.main_layout.control_panel.set_start_button_enabled(False)
            self.statusBar().showMessage(
                f"Ошибка инициализации модели '{model_name}'",
                3000
            )

    @pyqtSlot(object)
    def _update_siz_status(self, status):
        """Обновление статус-бара с улучшенной обработкой"""
        try:
            if status == "nothing":
                message = "СИЗ: ничего не обнаружено!"
            elif isinstance(status, list):
                if not status:  # Пустой список
                    message = "СИЗ: не обнаружены"
                else:
                    message = "СИЗ: все на местах" if all(status) else "СИЗ: обнаружены не все или не на своих местах!"
            else:
                message = "СИЗ: все на местах" if status else "СИЗ: проблемы обнаружены..."
            
            base_message = f"Модель: {self.current_model} | " if hasattr(self, 'current_model') and self.current_model else ""
            self.statusBar().showMessage(base_message + message)
            
        except Exception as e:
            self.logger.error(f"Status update error: {str(e)}")
            self.statusBar().showMessage("Ошибка обновления статуса")

    @pyqtSlot(str)
    def _on_model_selected(self, model_name):
        """Обработка выбора модели"""
        self.main_layout.control_panel.set_start_button_enabled(False)
        if model_name and model_name != "Нет доступных моделей":
            self.model_handler.load_model(model_name)

    @pyqtSlot(bool)
    def _update_status_bar(self, detected):
        """Обновление статуса СИЗ"""
        self.current_siz_status = detected
        status = f"Модель: {self.current_model} | СИЗ: {'обнаружены' if detected else 'отсутствуют!'}"
        self.statusBar().showMessage(status)
            
    def _load_initial_models(self):
        """Загрузка списка доступных моделей при старте"""
        models = self.model_handler.refresh_models_list()
        self.main_layout.model_selector.refresh_models(models)
        if models:
            self.statusBar().showMessage(f"Доступно моделей: {len(models)}", 3000)
        else:
            self.statusBar().showMessage("Модели не найдены!", 3000)

    def closeEvent(self, event):
        """Гарантированная очистка при закрытии"""
        self._on_stop_processing()  # Остановка обработки
        self.video_processor.cleanup()  # Освобождение ресурсов
        super().closeEvent(event)