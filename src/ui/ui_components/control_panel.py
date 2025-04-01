from PyQt6.QtWidgets import (QCheckBox, QPushButton, QHBoxLayout, QWidget, QDialog,
                            QLineEdit, QComboBox, QLabel, QFileDialog, QMessageBox)
from PyQt6.QtCore import pyqtSignal, Qt
from utils.logger import AppLogger 
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
        self.rtsp_storage = RtspStorage()
        self._start_button_enabled = False
        self._processing_active = False
        self.model_handler = None
        self._setup_ui()
    
    def set_model_handler(self, handler):
        self.model_handler = handler

    def _setup_ui(self):
        self.source_type = QComboBox()
        self.source_type.addItems(["Камера", "Видеофайл", "RTSP поток"])
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Введите индекс камеры (0, 1, ...)")
        
        self.browse_btn = QPushButton("Обзор")
        self.browse_btn.clicked.connect(self._browse_file)
        self.browse_btn.setProperty("class", "browse-btn")
        
        self.rtsp_combo = QComboBox()
        self._update_rtsp_combo()
        self.rtsp_combo.setToolTip("URL будет взят из выбранного RTSP потока")
        
        self.add_rtsp_btn = QPushButton("+")
        self.add_rtsp_btn.setFixedWidth(30)
        self.add_rtsp_btn.setToolTip("Добавить RTSP поток")
        self.add_rtsp_btn.clicked.connect(self._show_rtsp_dialog)
        self.add_rtsp_btn.setProperty("class", "add-rtsp-btn")
        
        self.landmarks_check = QCheckBox("Показывать ключевые точки")
        self.landmarks_check.setChecked(True)
        self.landmarks_check.stateChanged.connect(
            lambda state: self.toggle_landmarks.emit(state == Qt.CheckState.Checked.value)
        )
        
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("startButton")
        self.start_btn.setProperty("state", "disabled")
        
        layout = QHBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)
        
        layout.addWidget(QLabel("Источник:"), stretch=1)
        layout.addWidget(self.source_type, stretch=2)
        layout.addWidget(self.source_input, stretch=4)
        layout.addWidget(self.browse_btn, stretch=1)
        layout.addWidget(self.rtsp_combo, stretch=3)
        layout.addWidget(self.add_rtsp_btn, stretch=1)
        layout.addWidget(self.landmarks_check, stretch=2)
        layout.addWidget(self.start_btn, stretch=1)
        
        self.source_type.currentIndexChanged.connect(self._update_source_type)
        self.start_btn.clicked.connect(self._on_start_stop)
        self.rtsp_combo.currentTextChanged.connect(self._on_rtsp_selected)
        
        self._update_source_type(0)
    
    def _update_rtsp_combo(self):
        self.rtsp_combo.clear()
        rtsp_list = self.rtsp_storage.get_all_rtsp()
        self.rtsp_combo.addItems(rtsp_list.keys())
        
    def _show_rtsp_dialog(self):
        dialog = RtspManagerDialog(self.rtsp_storage, self)
        dialog.exec()
        self._update_rtsp_combo()
    
    def get_current_rtsp(self) -> dict:
        current_name = self.rtsp_combo.currentText()
        if current_name:
            return self.rtsp_storage.get_all_rtsp().get(current_name, {})
        return {}
    
    def _on_rtsp_selected(self, name):
        if name:
            rtsp_data = self.get_current_rtsp()
            if rtsp_data and rtsp_data.get("url"):
                self.source_input.setText(rtsp_data["url"])
                self.source_type.setCurrentIndex(2)
                self.source_input.setVisible(False)

    def set_start_button_enabled(self, enabled: bool):
        self._start_button_enabled = enabled
        state = "enabled" if enabled else "disabled"
        self.start_btn.setProperty("state", state)
        self._update_widget_style(self.start_btn)
    
    def set_processing_state(self, active: bool):
        self._processing_active = active
        
        widgets = [
            self.source_type,
            self.source_input,
            self.browse_btn,
            self.rtsp_combo,
            self.add_rtsp_btn,
            self.landmarks_check
        ]
        
        for widget in widgets:
            widget.setEnabled(not active)
            widget.setProperty("state", "disabled" if active else "enabled")
            self._update_widget_style(widget)
        
        self.start_btn.setText("Stop" if active else "Start")
        state = "stop" if active else ("enabled" if self._start_button_enabled else "disabled")
        self.start_btn.setProperty("state", state)
        self._update_widget_style(self.start_btn)

    def _update_widget_style(self, widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()
        
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
        elif is_rtsp and self.rtsp_combo.currentText():
            self._on_rtsp_selected(self.rtsp_combo.currentText())
        
    def _browse_file(self):
        if self._processing_active:
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите видеофайл", "",
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        
        if file_path:
            self.source_input.setText(file_path)
            self.video_source_changed.emit(file_path, 1)
            
    def _on_start_stop(self):
        if self._processing_active:
            self.stop_processing.emit()
        else:
            if not self.model_handler or not self.model_handler.current_model:
                QMessageBox.warning(self, "Ошибка", "Сначала выберите модель")
                return
                
            source_type = self.source_type.currentIndex()
            
            if source_type == 2:
                rtsp_data = self.get_current_rtsp()
                if not rtsp_data or not rtsp_data.get("url"):
                    QMessageBox.warning(self, "Ошибка", "RTSP не выбран")
                    return
                source = rtsp_data["url"]
            else:
                source = self.source_input.text().strip()
                if not source:
                    QMessageBox.warning(self, "Ошибка", "Введите данные для выбранного источника")
                    return
            
            self.video_source_changed.emit(source, source_type)
            self.start_processing.emit()