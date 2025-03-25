from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSlot, QTimer
from .model_handler import ModelHandler
from .video_processor import VideoProcessor
from src.yolo.yolo_detector import YOLODetector
from src.detection.face_detection import FaceDetector
from src.detection.pose_detection import PoseDetector
from src.detection.siz_detection import SIZDetector
from .ui_layout import MainLayout
from utils.logger import AppLogger

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

    def _setup_status_bar(self):
        """Настройка статус-бара с начальным сообщением"""
        self.statusBar().showMessage("Выберите модель для начала работы")
        self.current_model = None
        self.current_siz_status = None


    def _init_ui(self):
        self.setWindowTitle("PPE Detection System")
        self.setGeometry(100, 100, 800, 600)
        self.main_layout = MainLayout(self)  # Явно передаем self как parent
        self.setCentralWidget(self.main_layout)

    def _init_status_bar(self):
        """Инициализация статус-бара с постоянным сообщением"""
        self.statusBar().showMessage("Готов к работе")  # Стартовое сообщение
        self.current_siz_status = None

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
        self.main_layout.toggle_landmarks.connect(self.video_processor.toggle_landmarks)
        self.main_layout.model_selected.connect(self._on_model_selected)
        
        # Подключение сигналов от ModelHandler
        self.model_handler.model_loading.connect(self._on_model_loading)
        self.model_handler.model_loaded.connect(self._on_model_loaded)
        
        # Подключение сигналов к layout
        self.video_processor.update_frame_signal.connect(
            self.main_layout.video_display.update_frame
        )
        self.video_processor.siz_status_changed.connect(
            self._update_siz_status
        )

    @pyqtSlot()
    def _on_start_processing(self):
        """Обработка нажатия Start"""
        if not self.current_model:
            self.statusBar().showMessage("Ошибка: модель не выбрана!", 3000)
            return
            
        self.processing_active = True
        self.video_processor.start_processing()
        self.statusBar().showMessage(
            f"Обработка запущена | Модель: {self.current_model} | Статус СИЗ: проверка..."
        )

    @pyqtSlot()
    def _on_stop_processing(self):
        """Обработка нажатия Stop"""
        self.processing_active = False
        self.video_processor.stop_processing()
        
        # Обновляем статус после остановки
        status_message = f"Обработка остановлена | Модель: {self.current_model}"
        if self.current_siz_status is not None:
            status_message += f" | Последний статус СИЗ: {'обнаружены' if self.current_siz_status else 'отсутствуют!'}"
        
        self.statusBar().showMessage(status_message)

    @pyqtSlot(str)
    def _handle_model_selection(self, model_name):
        """Обработка выбора модели из селектора"""
        self.statusBar().showMessage(f"Выбрана модель: {model_name}")
        self.model_handler.load_model(model_name)

    @pyqtSlot(str)
    def _on_model_loading(self, model_name):
        """Обновление статуса при загрузке модели"""
        self.statusBar().showMessage(f"Загружаем модель: {model_name}...")

    @pyqtSlot(str, dict)
    def _on_model_loaded(self, model_name, model_info):
        """Обновление статуса после успешной загрузки модели"""
        if model_info:  # Проверяем что модель действительно загружена
            self.current_model = model_name
            success = self.video_processor.load_model(model_name, model_info)
            if success:
                self.statusBar().showMessage(
                    f"Модель '{model_name}' успешно загружена. Нажмите Start",
                    3000
                )
            else:
                self.statusBar().showMessage(
                    f"Ошибка инициализации модели '{model_name}'",
                    3000
                )

    @pyqtSlot(bool)
    def _update_siz_status(self, detected):
        """Обновление статуса СИЗ"""
        self.current_siz_status = detected
        if self.processing_active:
            status = "обнаружены" if detected else "отсутствуют!"
            self.statusBar().showMessage(
                f"Обработка | Модель: {self.current_model} | СИЗ: {status}"
            )

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

    def _restore_siz_status(self):
        """Восстановление статуса СИЗ после сообщения о загрузке"""
        if self.current_siz_status is not None:
            self._update_status_bar(self.current_siz_status)
        else:
            self.statusBar().showMessage(f"Модель '{self.current_model}' готова к работе")
            
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