from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSizePolicy, QScrollArea,
                            QComboBox, QPushButton, QCheckBox, QLineEdit, QMessageBox, QSpacerItem,
                            QFileDialog, QStatusBar)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
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
    manage_models_requested = pyqtSignal()

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
        self.setMinimumSize(1000, 800)
        
    def _init_ui(self):
        """Инициализация пользовательского интерфейса с улучшенной компоновкой"""
        self.setWindowTitle("Система обнаружения СИЗ")
        
        # Главный виджет и layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 1. Видео дисплей (с улучшенной адаптивностью)
        self._init_video_display()
        
        # 2. Панель выбора модели (с улучшенной компоновкой)
        self._init_model_panel()
        
        # 3. Панель управления (переработанная для лучшей адаптивности)
        self._init_control_panel()
        
        # 4. Статус бар
        self._init_status_bar()
        
        # Настройка видимости элементов
        self._update_source_type(0)
        
        # Установка политик размеров для адаптивности
        self._setup_size_policies()

    def _init_video_display(self):
        """Инициализация видео дисплея с адаптивным растяжением"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)  # Важно для контроля размеров
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Главный контейнер
        self.video_container = QWidget()
        self.video_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        # Основной layout с центрированием
        self.video_layout = QHBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        
        # Центрирующий контейнер
        self.center_container = QWidget()
        self.center_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        self.center_layout = QVBoxLayout(self.center_container)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.addStretch(1)  # Гибкое пространство сверху
        
        # Виджет для видео
        self.video_display = QLabel()
        self.video_display.setObjectName("videoDisplay")
        self.video_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_display.setMinimumSize(640, 480)
        
        self.center_layout.addWidget(self.video_display)
        self.center_layout.addStretch(1)  # Гибкое пространство снизу
        
        self.video_layout.addStretch(1)  # Гибкое пространство слева
        self.video_layout.addWidget(self.center_container)
        self.video_layout.addStretch(1)  # Гибкое пространство справа
        
        self.scroll_area.setWidget(self.video_container)
        self.main_layout.addWidget(self.scroll_area, stretch=1)

    def _init_model_panel(self):
        """Инициализация панели выбора модели"""
        self.model_panel = QWidget()
        model_layout = QHBoxLayout(self.model_panel)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(10)
        
        self.model_label = QLabel("Модель:   ")
        self.model_combo = QComboBox()
        self.model_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.activate_model_btn = QPushButton("Активировать")
        
        self.manage_models_btn = QPushButton("Управление моделями")
        
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.model_combo, stretch=1)
        model_layout.addWidget(self.activate_model_btn)
        model_layout.addWidget(self.manage_models_btn)
        
        self.main_layout.addWidget(self.model_panel)

    def _init_control_panel(self):
        """Инициализация панели управления с улучшенной адаптивностью"""
        self.control_panel = QWidget()
        control_layout = QVBoxLayout(self.control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)
        
        # Верхняя строка: выбор источника
        source_row = QWidget()
        source_layout = QHBoxLayout(source_row)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.setSpacing(10)
        
        self.source_label = QLabel("Источник:")
        self.source_type = QComboBox()
        self.source_type.addItems(["Камера", "Видеофайл", "RTSP поток"])
        self.source_type.setFixedWidth(120)
        
        self.source_input = QLineEdit()
        self.source_input.setProperty("valid", "unknown")
        self.source_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.browse_btn = QPushButton("Обзор")
        
        self.rtsp_combo = QComboBox()
        self.rtsp_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.add_rtsp_btn = QPushButton("+")
        
        source_layout.addWidget(self.source_label)
        source_layout.addWidget(self.source_type)
        source_layout.addWidget(self.source_input, stretch=1)
        source_layout.addWidget(self.browse_btn)
        source_layout.addWidget(self.rtsp_combo, stretch=1)
        source_layout.addWidget(self.add_rtsp_btn)
        
        # Нижняя строка: управление
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        self.landmarks_check = QCheckBox("Показывать ключевые точки")
        self.landmarks_check.setChecked(False)
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        self.start_btn = QPushButton("Запустить анализ")
        self.start_btn.setObjectName("startButton")
        self.start_btn.setEnabled(False)
        
        bottom_layout.addWidget(self.landmarks_check)
        bottom_layout.addItem(spacer)
        bottom_layout.addWidget(self.start_btn)
        
        control_layout.addWidget(source_row)
        control_layout.addWidget(bottom_row)
        
        self.main_layout.addWidget(self.control_panel)

    def _init_status_bar(self):
        """Инициализация статус бара с небольшими улучшениями"""
        self.status_bar = QStatusBar()
        self.status_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStatusBar(self.status_bar)
        
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setObjectName("themeButton")
        self.theme_btn.setFixedSize(30, 30)
        self.status_bar.addPermanentWidget(self.theme_btn)

    def _setup_size_policies(self):
        """Настройка политик размеров для адаптивности"""
        # Виджеты, которые должны расширяться по горизонтали
        expand_horizontal = [
            self.video_display,
            self.model_combo,
            self.source_input,
            self.rtsp_combo
        ]
        
        for widget in expand_horizontal:
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Главное окно должно сохранять пропорции
        self.central_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _setup_validation(self):
        """Настраивает валидацию в реальном времени (без изменений)"""
        self.source_input.textChanged.connect(self._validate_current_input)
        self.source_type.currentIndexChanged.connect(self._update_validation)
        self._update_validation()

    def _update_validation(self):
        """Обновляет тип валидации при изменении типа источника (без изменений)"""
        self._validate_current_input(self.source_input.text())

    def _validate_current_input(self, text):
        """Валидирует текущий ввод (без изменений)"""
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
            
            # Подключение изменения модели
            self.model_combo.currentTextChanged.connect(self._update_current_model)
            
            self._connections_initialized = True
        
        # Оставляем только эти подключения
        self.source_type.currentIndexChanged.connect(self._update_source_type)
        self.landmarks_check.stateChanged.connect(
            lambda state: self.toggle_landmarks.emit(state == Qt.CheckState.Checked.value)
        )
        self.add_rtsp_btn.clicked.connect(self.add_rtsp_requested.emit)
        self.rtsp_combo.currentTextChanged.connect(self.rtsp_selected.emit)
    
    def _update_current_model(self, model_name):
        """Обновляет текущее название модели и состояние кнопки"""
        self._current_model_name = model_name
        # Делаем кнопку неактивной при изменении модели
        self.start_btn.setEnabled(False)
        # Обновляем стиль
        self._update_start_button_style()

    def _update_start_button_style(self):
        """Обновляет стиль кнопки запуска"""
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.start_btn.update()

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
                self.source_input.text() or "",  # Начинаем с текущего пути если есть
                "Video Files (*.mp4 *.avi *.mov *.mkv)"
            )
            if file_path:
                self.source_input.setText(file_path)

    def update_frame(self, q_image):
        """Обновление кадра с адаптивным растяжением"""
        if not q_image.isNull():
            # Рассчитываем максимальные размеры с сохранением пропорций
            container_size = self.scroll_area.viewport().size()
            aspect_ratio = q_image.width() / q_image.height()
            
            # Вычисляем максимально возможные размеры
            max_width = container_size.width()
            max_height = int(max_width / aspect_ratio)
            
            if max_height > container_size.height():
                max_height = container_size.height()
                max_width = int(max_height * aspect_ratio)
            
            # Масштабируем изображение
            scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                max_width, max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.video_display.setPixmap(scaled_pixmap)
            self.video_display.setFixedSize(scaled_pixmap.size())
            
            # Устанавливаем минимальный размер контейнера
            self.video_container.setMinimumSize(container_size)
        
    def show_message(self, message, timeout=0):
        self.status_bar.showMessage(message, timeout)
        
    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)