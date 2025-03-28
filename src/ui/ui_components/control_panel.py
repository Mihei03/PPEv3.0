from PyQt6.QtWidgets import (QCheckBox, QPushButton, QHBoxLayout, QWidget,
                            QLineEdit, QComboBox, QLabel, QFileDialog, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt
from utils.logger import AppLogger 

class ControlPanel(QWidget):
    start_processing = pyqtSignal()
    stop_processing = pyqtSignal()
    toggle_landmarks = pyqtSignal(bool)
    video_source_changed = pyqtSignal(str, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._start_button_enabled = False
        self._processing_active = False
        self.logger = AppLogger.get_logger()
        
    def _setup_ui(self):
        self.source_type = QComboBox()
        self.source_type.addItems(["Камера", "Видеофайл", "RTSP поток"])
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Введите индекс камеры (0, 1, ...)")
        
        self.browse_btn = QPushButton("Обзор")
        self.browse_btn.clicked.connect(self._browse_file)
        
        self.landmarks_check = QCheckBox("Показывать ключевые точки")
        self.landmarks_check.setChecked(True)
        self.landmarks_check.stateChanged.connect(
            lambda state: (self.toggle_landmarks.emit(state == Qt.CheckState.Checked.value),
                self.logger.info(f"Landmarks checkbox state changed: {state == Qt.CheckState.Checked.value}")
        ))
        self.start_btn = QPushButton("Start")
        self.start_btn.setEnabled(False)  # По умолчанию отключена
        
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Источник:"))
        layout.addWidget(self.source_type)
        layout.addWidget(self.source_input)
        layout.addWidget(self.browse_btn)
        layout.addWidget(self.landmarks_check)
        layout.addWidget(self.start_btn)
        
        self.source_type.currentIndexChanged.connect(self._update_source_type)
        self.start_btn.clicked.connect(self._on_start_stop)
        self._update_source_type(0)
        
    def set_start_button_enabled(self, enabled: bool):
        """Устанавливает состояние кнопки Start с проверкой"""
        # Всегда разрешаем остановку, но запуск только при enabled=True
        if self._processing_active:
            self.start_btn.setEnabled(True)  # Для кнопки Stop
        else:
            self.start_btn.setEnabled(enabled)  # Для кнопки Start
            self.start_btn.setStyleSheet(
                "background-color: #4CAF50;" if enabled 
                else "background-color: #cccccc;"
            )
    
    def set_processing_state(self, active: bool):
        """Блокировка интерфейса во время обработки"""
        self._processing_active = active
        self.source_type.setEnabled(not active)
        self.source_input.setEnabled(not active)
        self.browse_btn.setEnabled(not active)
        self.start_btn.setText("Stop" if active else "Start")
        self.start_btn.setEnabled(True)

    def is_start_button_enabled(self) -> bool:
        """Возвращает текущее состояние кнопки Start"""
        return self._start_button_enabled
        
    def _update_source_type(self, index):
        """Обновляет интерфейс при смене типа источника"""
        placeholders = [
            "Введите индекс камеры (0, 1, ...)",
            "Введите путь к видеофайлу",
            "Введите RTSP URL (rtsp://...)"
        ]
        self.source_input.setPlaceholderText(placeholders[index])
        self.browse_btn.setVisible(index in [1, 3])
        self.source_input.clear()
        
        # Для камеры по умолчанию устанавливаем 0
        if index == 0:
            self.source_input.setText("0")
        
    def _browse_file(self):
        """Обработчик кнопки 'Обзор' с полной синхронизацией аргументов"""
        if self._processing_active:
            return
            
        current_type = self.source_type.currentIndex()
        if current_type == 1:  # Видеофайл
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Выберите видеофайл", "",
                "Video Files (*.mp4 *.avi *.mov *.mkv)"
            )
            
        if file_path:
            self.source_input.setText(file_path)
            # Передаем ОБА аргумента: путь и тип источника
            selected_type = self.source_type.currentIndex()
            self.video_source_changed.emit(file_path, selected_type)
            
    def _on_start_stop(self):
        """Обработчик кнопки Start/Stop"""
        if self._processing_active:
            self.stop_processing.emit()
        else:
            source = self.source_input.text().strip()
            selected_type = self.source_type.currentIndex()
            if source:
                # Всегда передаем оба параметра
                self.video_source_changed.emit(source, selected_type)
                self.start_processing.emit()
            else:
                QMessageBox.warning(self, "Ошибка", "Введите данные для выбранного источника")
                
    def _validate_and_emit_source(self, source: str):
        """Проверяет и отправляет источник"""
        if not self._processing_active and source:
            self.video_source_changed.emit(source)