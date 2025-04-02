from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
                            QComboBox, QPushButton, QCheckBox, QLineEdit, QMessageBox,
                            QFileDialog, QStatusBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage
from utils.logger import AppLogger
import os

class MainWindowUI(QMainWindow):
    # Сигналы
    start_processing = pyqtSignal()
    stop_processing = pyqtSignal()
    toggle_landmarks = pyqtSignal(bool)
    model_selected = pyqtSignal(str)
    load_model_requested = pyqtSignal()
    video_source_changed = pyqtSignal(str, int)
    rtsp_selected = pyqtSignal(str)
    add_rtsp_requested = pyqtSignal()

    def set_style_sheet(self, stylesheet):
        self.setStyleSheet(stylesheet)
        for child in self.findChildren(QWidget):
            child.setStyleSheet(stylesheet)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connections_initialized = False  # Инициализируем атрибут
        self._init_ui()
        self._connect_signals()
        self._setup_validation()

    def _init_ui(self):
        """Инициализация пользовательского интерфейса с проверкой всех атрибутов"""
        self.setWindowTitle("Система обнаружения СИЗ")
        self.setGeometry(100, 100, 800, 600)
        
        # Главный виджет и layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 1. Видео дисплей
        self._init_video_display()
        
        # 2. Панель выбора модели
        self._init_model_panel()
        
        # 3. Панель управления
        self._init_control_panel()
        
        # 4. Статус бар и тема
        self._init_status_bar()
        
        # Настройка видимости элементов
        self._update_source_type(0)
        
        # Установка стилей
        self._apply_initial_styles()

    def _init_video_display(self):
        """Инициализация видео дисплея"""
        self.video_display = QLabel()
        self.video_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_display.setMinimumSize(640, 480)
        self.video_display.setStyleSheet("background-color: black;")
        self.main_layout.addWidget(self.video_display)

    def _init_model_panel(self):
        """Инициализация панели выбора модели"""
        self.model_panel = QWidget()
        model_layout = QHBoxLayout(self.model_panel)
        
        self.model_label = QLabel("Модели:")
        self.model_combo = QComboBox()
        self.activate_model_btn = QPushButton("Активировать модель")
        self.add_model_btn = QPushButton("Добавить модель")
        
        # Настройка свойств
        self.model_label.setObjectName("modelLabel")
        self.activate_model_btn.setEnabled(False)
        
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(self.activate_model_btn)
        model_layout.addWidget(self.add_model_btn)
        
        self.main_layout.addWidget(self.model_panel)

    def _init_control_panel(self):
        """Инициализация панели управления"""
        self.control_panel = QWidget()
        control_layout = QHBoxLayout(self.control_panel)
        
        # Создание элементов
        self.source_label = QLabel("Источник:")
        self.source_type = QComboBox()
        self.source_type.addItems(["Камера", "Видеофайл", "RTSP поток"])
        self.source_input = QLineEdit()
        self.browse_btn = QPushButton("Обзор")
        self.rtsp_combo = QComboBox()
        self.add_rtsp_btn = QPushButton("+")
        self.landmarks_check = QCheckBox("Показывать ключевые точки")
        self.start_btn = QPushButton("Start")
        
        # Настройка свойств
        self.source_input.setPlaceholderText("Введите индекс камеры (0, 1, ...)")
        self.add_rtsp_btn.setFixedWidth(30)
        self.landmarks_check.setChecked(True)
        self.start_btn.setObjectName("startButton")
        self.start_btn.setEnabled(False)
        
        # Добавление в layout
        control_layout.addWidget(self.source_label)
        control_layout.addWidget(self.source_type)
        control_layout.addWidget(self.source_input)
        control_layout.addWidget(self.browse_btn)
        control_layout.addWidget(self.rtsp_combo)
        control_layout.addWidget(self.add_rtsp_btn)
        control_layout.addWidget(self.landmarks_check)
        control_layout.addWidget(self.start_btn)
        
        self.main_layout.addWidget(self.control_panel)

    def _init_status_bar(self):
        """Инициализация статус бара и кнопки темы"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.theme_btn = QPushButton()
        self.theme_btn.setObjectName("themeButton")
        self.status_bar.addPermanentWidget(self.theme_btn)

    def _apply_initial_styles(self):
        """Применение начальных стилей"""
        # Установка начального текста кнопки темы
        self.theme_btn.setText("🌙")
        
        # Настройка отступов
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

    def _setup_validation(self):
        """Настраивает валидацию в реальном времени для всех полей ввода"""
        # Подключаем сигналы изменения текста
        self.source_input.textChanged.connect(self._validate_current_input)
        self.source_type.currentIndexChanged.connect(self._update_validation)
        
        # Инициализируем валидацию
        self._update_validation()

    def _update_validation(self):
        """Обновляет тип валидации при изменении типа источника"""
        self._validate_current_input(self.source_input.text())

    def _validate_current_input(self, text):
        """Валидирует текущий ввод в зависимости от выбранного типа"""
        source_type = self.source_type.currentIndex()
        text = text.strip()
        
        try:
            if source_type == 0:  # Камера
                is_valid, tooltip = self._validate_camera(text)
            elif source_type == 1:  # Видеофайл
                is_valid, tooltip = self._validate_video(text)
            elif source_type == 2:  # RTSP
                is_valid, tooltip = self._validate_rtsp(text)
            else:
                is_valid, tooltip = False, "Неизвестный тип источника"
        except Exception as e:
            is_valid, tooltip = False, f"Ошибка валидации: {str(e)}"
        
        self.source_input.setToolTip(tooltip)
        self._set_input_validity(is_valid)
        

    def _validate_camera(self, text):
        """Проверяет валидность индекса камеры"""
        try:
            index = int(text)
            valid = index >= 0
            tooltip = "Валидный индекс камеры" if valid else "Индекс камеры должен быть ≥ 0"
            return valid, tooltip
        except ValueError:
            return False, "Введите числовой индекс камеры (0, 1, ...)"

    def _validate_video(self, text):
        """Проверяет валидность пути к видеофайлу"""
        if not text:
            return False, "Введите путь к видеофайлу"
        
        valid = text.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))
        if not valid:
            return False, "Поддерживаемые форматы: .mp4, .avi, .mov, .mkv"
        
        exists = os.path.exists(text)
        return exists, "Файл найден" if exists else "Файл не существует"

    def _validate_rtsp(self, text):
        """Проверяет валидность RTSP URL"""
        if not text:
            return False, "Введите RTSP URL"
        
        valid = text.startswith('rtsp://') and len(text) > 10
        return valid, "Валидный RTSP URL" if valid else "URL должен начинаться с rtsp:// и быть длиннее 10 символов"

    def _set_input_validity(self, is_valid):
        """Устанавливает стиль поля ввода на основе валидности"""
        try:
            self.source_input.setProperty("valid", str(is_valid).lower())
            self.source_input.style().unpolish(self.source_input)
            self.source_input.style().polish(self.source_input)
            self.source_input.update()
        except Exception as e:
            print(f"Ошибка применения стиля: {e}")

    def update_theme(self, dark_mode):
        """Обновление темы интерфейса"""
        try:
            # Устанавливаем или удаляем класс dark-mode для главного окна
            if dark_mode:
                self.setProperty("class", "dark-mode")
            else:
                self.setProperty("class", "")
                
            # Обновляем стили всех дочерних виджетов
            for child in self.findChildren(QWidget):
                child.style().unpolish(child)
                child.style().polish(child)
                child.update()
                
        except Exception as e:
            AppLogger.get_logger().error(f"Ошибка обновления темы: {str(e)}")
            
    def _connect_signals(self):
        if not self._connections_initialized:
            # Подключение кнопки активации
            self.activate_model_btn.clicked.connect(
            lambda: self.model_selected.emit(self.model_combo.currentText())
        )
            
            # Подключение изменения модели только для обновления текущего выбора
            self.model_combo.currentTextChanged.connect(self._update_current_model)
            
            self._connections_initialized = True

        self.source_type.currentIndexChanged.connect(self._update_source_type)
        self.browse_btn.clicked.connect(self._browse_file_ui)
        self.add_model_btn.clicked.connect(self.load_model_requested.emit)
        
        
        self.landmarks_check.stateChanged.connect(lambda state: self.toggle_landmarks.emit(state == Qt.CheckState.Checked.value))
        self.add_rtsp_btn.clicked.connect(self.add_rtsp_requested.emit)
        self.rtsp_combo.currentTextChanged.connect(self.rtsp_selected.emit)
    
    def _update_current_model(self, model_name):
        """Только сохраняет текущий выбор, не активирует"""
        self._current_model_name = model_name

    def _activate_model(self):
        """Активация только по кнопке"""
        if hasattr(self, '_current_model_name'):
            self.model_selected.emit(self._current_model_name)

    def _update_source_type(self, index):
        placeholders = [
            "Введите индекс камеры (0, 1, ...)",
            "Введите путь к видеофайлу",
            "Введите RTSP URL (rtsp://...)"
        ]
        self.source_input.setPlaceholderText(placeholders[index])
        
        is_file = index == 1
        is_rtsp = index == 2
        
        self.browse_btn.setVisible(is_file)
        self.rtsp_combo.setVisible(is_rtsp)
        self.add_rtsp_btn.setVisible(is_rtsp)
        self.source_input.setVisible(not is_rtsp)
        
        if index == 0:
            self.source_input.setText("0")

    def _browse_file_ui(self):
        """Только открытие диалога и установка текста"""
        if self.source_type.currentIndex() == 1:  # Только для видеофайлов
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите видеофайл",
                "",
                "Video Files (*.mp4 *.avi *.mov *.mkv)"
            )
            if file_path:
                self.source_input.setText(file_path)

    def update_frame(self, q_image):
        self.video_display.setPixmap(QPixmap.fromImage(q_image))
        
    def show_message(self, message, timeout=0):
        self.status_bar.showMessage(message, timeout)
        
    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)