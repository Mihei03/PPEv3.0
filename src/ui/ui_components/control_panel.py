from PyQt6.QtWidgets import (QCheckBox, QPushButton, QHBoxLayout, QWidget, QDialog,
                            QLineEdit, QComboBox, QLabel, QFileDialog, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt
from detection.input_validator import InputValidator
from utils.logger import AppLogger 
from ui.ui_components.rtsp_storage import RtspStorage
from .rtsp_manager import RtspManagerDialog
from .rtsp_storage import RtspStorage

class ControlPanel(QWidget):
    start_processing = pyqtSignal()
    stop_processing = pyqtSignal()
    toggle_landmarks = pyqtSignal(bool)
    video_source_changed = pyqtSignal(str, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = AppLogger.get_logger()
        self.rtsp_storage = RtspStorage()  # Инициализируем ПЕРЕД _setup_ui()
        self._start_button_enabled = False
        self._processing_active = False
        self._setup_ui()  # Вызываем после инициализации rtsp_storage
        
    def _setup_ui(self):
        self.source_type = QComboBox()
        self.source_type.addItems(["Камера", "Видеофайл", "RTSP поток"])
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Введите индекс камеры (0, 1, ...)")
        
        self.browse_btn = QPushButton("Обзор")
        self.browse_btn.clicked.connect(self._browse_file)
        
        # RTSP элементы управления
        self.rtsp_combo = QComboBox()
        self._update_rtsp_combo()
        self.rtsp_combo.setToolTip("URL будет взят из выбранного RTSP потока")
        self.add_rtsp_btn = QPushButton("+")
        self.add_rtsp_btn.setFixedWidth(30)
        self.add_rtsp_btn.setToolTip("Добавить RTSP поток")
        self.add_rtsp_btn.clicked.connect(self._show_rtsp_dialog)
        
        rtsp_layout = QHBoxLayout()
        rtsp_layout.addWidget(self.rtsp_combo)
        rtsp_layout.addWidget(self.add_rtsp_btn)
        
        self.landmarks_check = QCheckBox("Показывать ключевые точки")
        self.landmarks_check.setChecked(True)
        self.landmarks_check.stateChanged.connect(
            lambda state: self.toggle_landmarks.emit(state == Qt.CheckState.Checked.value)
        )
        
        self.start_btn = QPushButton("Start")
        self.start_btn.setEnabled(False)
        
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("Источник:"))
        layout.addWidget(self.source_type)
        layout.addWidget(self.source_input)
        layout.addWidget(self.browse_btn)
        layout.addLayout(rtsp_layout)
        layout.addWidget(self.landmarks_check)
        layout.addWidget(self.start_btn)
        
        self.source_type.currentIndexChanged.connect(self._update_source_type)
        self.start_btn.clicked.connect(self._on_start_stop)
        self.rtsp_combo.currentTextChanged.connect(self._on_rtsp_selected)
        
        self._update_source_type(0)
    
    def _update_rtsp_combo(self):
        """Обновляет список RTSP в комбобоксе"""
        self.rtsp_combo.clear()
        rtsp_list = self.rtsp_storage.get_all_rtsp()
        self.rtsp_combo.addItems(rtsp_list.keys())
        
    def _show_rtsp_dialog(self):
        """Показывает диалог добавления RTSP"""
        dialog = RtspManagerDialog(self.rtsp_storage, self)
        dialog.exec()
        self._update_rtsp_combo()
    
    def get_current_rtsp(self) -> dict:
        """Возвращает данные текущего выбранного RTSP потока"""
        current_name = self.rtsp_combo.currentText()
        if current_name:
            return self.rtsp_storage.get_all_rtsp().get(current_name, {})
        return {}
    
    def _on_rtsp_selected(self, name):
        """Обрабатывает выбор RTSP из списка"""
        if name:
            rtsp_data = self.get_current_rtsp()  # Используем новый метод
            if rtsp_data and rtsp_data.get("url"):
                self.source_input.setText(rtsp_data["url"])
                self.source_type.setCurrentIndex(2)  # Устанавливаем тип "RTSP поток"
                self.source_input.setVisible(False)  # Скрываем поле ввода для RTSP

    def set_start_button_enabled(self, enabled: bool):
        """Устанавливает состояние кнопки Start"""
        if self._processing_active:
            self.start_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(enabled)
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
        self.rtsp_combo.setEnabled(not active)
        self.add_rtsp_btn.setEnabled(not active)
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
        
        # Управление видимостью элементов
        is_camera = index == 0
        is_file = index == 1
        is_rtsp = index == 2
        
        self.browse_btn.setVisible(is_file)
        self.rtsp_combo.setVisible(is_rtsp)
        self.add_rtsp_btn.setVisible(is_rtsp)
        self.source_input.setVisible(not is_rtsp)  # Скрываем для RTSP
        
        if is_camera:
            self.source_input.setText("0")
        elif is_rtsp and self.rtsp_combo.currentText():
            self._on_rtsp_selected(self.rtsp_combo.currentText())
        
    def _browse_file(self):
        """Обработчик кнопки 'Обзор'"""
        if self._processing_active:
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите видеофайл", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        
        if file_path:
            self.source_input.setText(file_path)
            self.video_source_changed.emit(file_path, 1)  # 1 = Видеофайл
            
    def _on_start_stop(self):
        """Обработчик кнопки Start/Stop"""
        if self._processing_active:
            self.stop_processing.emit()
        else:
            source_type = self.source_type.currentIndex()
            
            if source_type == 2:  # RTSP поток
                rtsp_data = self.get_current_rtsp()
                if not rtsp_data or not rtsp_data.get("url"):
                    QMessageBox.warning(self, "Ошибка", " RTSP не выбран")
                    return
                source = rtsp_data["url"]
            else:
                source = self.source_input.text().strip()
                if not source:
                    QMessageBox.warning(self, "Ошибка", "Введите данные для выбранного источника")
                    return
            
            self.video_source_changed.emit(source, source_type)
            self.start_processing.emit()
                    
    def _validate_and_emit_source(self, source: str):
        """Проверяет и отправляет источник"""
        if not self._processing_active and source:
            self.video_source_changed.emit(source)