from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
                            QLabel, QComboBox, QPushButton, 
                            QCheckBox, QLineEdit, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer
import os

class ControlPanel:
    def __init__(self, main_window):
        self.main_window = main_window
        self.panel = QWidget()
        self.source_type = None
        self.source_input = None
        self.browse_btn = None
        self.rtsp_combo = None
        self.add_rtsp_btn = None
        self.start_btn = None
        self._setup_panel()
        
    def _setup_panel(self):
        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Source row
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
        self.source_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Fixed
        )
        
        self.browse_btn = QPushButton("Обзор")
        self.rtsp_combo = QComboBox()
        self.rtsp_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Fixed
        )
        self.add_rtsp_btn = QPushButton("Управление RTSP")
        
        source_layout.addWidget(self.source_label)
        source_layout.addWidget(self.source_type)
        source_layout.addWidget(self.source_input, stretch=1)
        source_layout.addWidget(self.browse_btn)
        source_layout.addWidget(self.rtsp_combo, stretch=1)
        source_layout.addWidget(self.add_rtsp_btn)
        
        # Bottom row
        bottom_row = QWidget()
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(10)
        
        self.landmarks_check = QCheckBox("Показывать ключевые точки")
        self.landmarks_check.setChecked(False)
        spacer = QSpacerItem(20, 20, 
                            QSizePolicy.Policy.Expanding, 
                            QSizePolicy.Policy.Minimum)
        
        self.start_btn = QPushButton("Запустить анализ")
        self.start_btn.setObjectName("startButton")
        self.start_btn.setEnabled(False)
        
        bottom_layout.addWidget(self.landmarks_check)
        bottom_layout.addItem(spacer)
        bottom_layout.addWidget(self.start_btn)
        
        layout.addWidget(source_row)
        layout.addWidget(bottom_row)
        
        # Setup validation
        self._setup_validation()
        self._update_source_type(0)
    
    def _setup_validation(self):
        self.source_input.textChanged.connect(self._validate_current_input)
        self.source_type.currentIndexChanged.connect(self._update_source_type)
        self.start_btn.clicked.connect(self._handle_start_btn_click)
        self.rtsp_combo.currentTextChanged.connect(self._validate_rtsp_selection)
    
    def _validate_rtsp_selection(self):
        if self.source_type.currentIndex() == 2:  # Если выбран RTSP
            if hasattr(self.main_window, 'rtsp_manager'):
                self.main_window.rtsp_manager.validate_rtsp_selection()

    def _handle_start_btn_click(self):
        """Обработчик клика на кнопку запуска, когда она заблокирована"""
        if not self.start_btn.isEnabled():
            source_type = self.source_type.currentIndex()
            message = "Для запуска анализа необходимо:\n"
            
            if source_type == 2:  # RTSP
                rtsp_name = self.rtsp_combo.currentText()
                if not rtsp_name or rtsp_name == "Нет сохраненных RTSP":
                    message += "1. Выберите RTSP поток из списка\n"
                else:
                    message += "1. Для выбранного RTSP потока должна быть назначена модель\n"
            else:
                message += "1. Укажите корректный источник видео\n"
            
            message += "2. Выберите и активируйте модель"
            
            QMessageBox.information(
                self.panel,
                "Нельзя запустить анализ",
                message,
                QMessageBox.StandardButton.Ok
            )

    def _update_source_type(self, index):
        placeholders = [
            "Введите индекс камеры (0, 1, ...)",
            "Введите путь к видеофайлу или выберите его через 'Обзор'",
            "Выберите RTSP поток"
        ]
        self.source_input.setPlaceholderText(placeholders[index])
        
        is_file = index == 1
        is_rtsp = index == 2
        
        self.browse_btn.setVisible(is_file)
        self.rtsp_combo.setVisible(is_rtsp)
        self.add_rtsp_btn.setVisible(is_rtsp)
        self.source_input.setVisible(not is_rtsp)
        
        # Очищаем поле при переключении на файл или RTSP
        if index != 0:
            self.source_input.clear()
        else:
            self.source_input.setText("0")
        
        # Для RTSP сразу запускаем проверку
        if is_rtsp and hasattr(self.main_window, 'rtsp_manager'):
            QTimer.singleShot(100, self._delayed_rtsp_validation)
        
        # Общая валидация для всех типов источников
        self._validate_current_input(self.source_input.text())

    def _delayed_rtsp_validation(self):
        """Отложенная валидация RTSP для корректного обновления UI"""
        if hasattr(self.main_window, 'rtsp_manager'):
            self.main_window.rtsp_manager.validate_rtsp_selection()

    def _validate_current_input(self, text):
        source_type = self.source_type.currentIndex()
        text = text.strip()
        
        if source_type == 1 and text == "0":
            self._set_input_validity(False)
            self.source_input.setToolTip("Введите путь к видеофайлу или выберите его через 'Обзор'")
            return
        
        try:
            if source_type == 0:
                is_valid, tooltip = self._validate_camera(text)
            elif source_type == 1:
                is_valid, tooltip = self._validate_video(text)
            elif source_type == 2:
                is_valid, tooltip = self._validate_rtsp(text)
            else:
                is_valid, tooltip = False, "Неизвестный тип источника"
        except Exception as e:
            is_valid, tooltip = False, f"Ошибка валидации: {str(e)}"
        
        self.source_input.setToolTip(tooltip)
        self._set_input_validity(is_valid)
    
    def _validate_camera(self, text):
        try:
            index = int(text)
            valid = index >= 0
            tooltip = "Валидный индекс камеры" if valid else "Индекс камеры должен быть ≥ 0"
            return valid, tooltip
        except ValueError:
            return False, "Введите числовой индекс камеры (0, 1, ...)"

    def _validate_video(self, text):
        if not text or text.strip() == "0":
            return False, "Введите путь к видеофайлу или выберите его через 'Обзор'"
        
        valid = text.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))
        if not valid:
            return False, "Поддерживаемые форматы: .mp4, .avi, .mov, .mkv"
        
        exists = os.path.exists(text)
        return exists, "Файл найден" if exists else "Файл не существует"

    def _validate_rtsp(self, text):
        if not text:
            return False, "Введите RTSP URL"
        
        valid = text.startswith('rtsp://') and len(text) > 10
        return valid, "Валидный RTSP URL" if valid else "URL должен начинаться с rtsp:// и быть длиннее 10 символов"

    def _set_input_validity(self, is_valid):
        self.source_input.setProperty("valid", "true" if is_valid else "false")
        self.source_input.style().unpolish(self.source_input)
        self.source_input.style().polish(self.source_input)
        self.source_input.update()