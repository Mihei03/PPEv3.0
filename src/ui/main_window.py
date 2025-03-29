from PyQt6.QtWidgets import QMainWindow, QMessageBox
from PyQt6.QtCore import pyqtSlot, QTimer
from .model_handler import ModelHandler
from .video_processor import VideoProcessor
from src.yolo.yolo_detector import YOLODetector
from src.detection.face_detection import FaceDetector
from src.detection.pose_detection import PoseDetector
from src.detection.siz_detection import SIZDetector
from .ui_layout import MainLayout
from utils.logger import AppLogger
import cv2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._init_detectors()
        self._setup_connections()
        self._init_status_vars()
        self._load_initial_models()
        self.logger = AppLogger.get_logger() 
        
    def _init_status_vars(self):
        """Инициализация переменных статуса"""
        self.current_model = None
        self.current_siz_status = None
        self.processing_active = False
        self.statusBar().showMessage("Выберите модель и нажмите Start")

    def _init_ui(self):
        self.setWindowTitle("Система обнаружения СИЗ")
        self.setGeometry(100, 100, 800, 600)
        self.main_layout = MainLayout(self)  # Явно передаем self как parent
        self.setCentralWidget(self.main_layout)

    def _init_detectors(self):
        self.yolo = YOLODetector()
        self.pose = PoseDetector()
        self.face = FaceDetector()
        self.siz = SIZDetector()
        
        self.video_processor = VideoProcessor()
        self.video_processor.set_detectors(self.yolo, self.face, self.pose, self.siz)
        
        self.model_handler = ModelHandler(self)

    def _setup_connections(self):
        """Настройка всех соединений"""
        # Подключение сигналов от layout
        self.main_layout.start_processing.connect(self._on_start_processing)
        self.main_layout.stop_processing.connect(self._on_stop_processing)
        self.main_layout.toggle_landmarks.connect(
            lambda state: (self.video_processor.toggle_landmarks(state),
                self.logger.info(f"Landmarks visibility: {state}"))
        )
        self.main_layout.model_selected.connect(self._on_model_selected)
        self.main_layout.model_selector.load_model_requested.connect(self._load_new_model)

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
            self.main_layout.model_selector.refresh_models(models)
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
        """Запуск только при успешной проверке"""
        if not self.current_model:
            self.statusBar().showMessage("Сначала выберите модель!", 3000)
            return
            
        # Дополнительная проверка перед стартом
        if not self.video_processor.is_source_ready():
            self.statusBar().showMessage("Источник не готов!", 3000)
            self.main_layout.control_panel.set_start_button_enabled(False)
            return
            
        self.processing_active = True
        self.main_layout.control_panel.set_processing_state(True)
        self.video_processor.start_processing()
        self.statusBar().showMessage("Обработка запущена", 3000)

    @pyqtSlot()
    def _on_stop_processing(self):
        """Обработка остановки обработки"""
        self.processing_active = False
        self.main_layout.control_panel.set_processing_state(False)
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
        """Обработка успешной загрузки модели"""
        self.current_model = model_name
        success = self.video_processor.load_model(model_name, model_info)
        
        if success:
            self.statusBar().showMessage(
                f"Модель '{model_name}' успешно загружена. Нажмите Start",
                3000
            )
            # Активируем кнопку через метод ControlPanel
            if hasattr(self.main_layout, 'control_panel'):
                self.main_layout.control_panel.set_start_button_enabled(True)
        else:
            self.statusBar().showMessage(
                f"Ошибка инициализации модели '{model_name}'",
                3000
            )
            if hasattr(self.main_layout, 'control_panel'):
                self.main_layout.control_panel.set_start_button_enabled(False)

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
        """Обработка выбора модели из селектора"""
        self.statusBar().showMessage(f"Выбрана модель: {model_name}")
        success = self.model_handler.load_model(model_name)
        if not success:
            self.statusBar().showMessage(f"Ошибка загрузки модели: {model_name}", 3000)

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