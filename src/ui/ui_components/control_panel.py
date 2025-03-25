from PyQt6.QtWidgets import QCheckBox, QPushButton, QHBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal

class ControlPanel(QWidget):
    start_processing = pyqtSignal()
    stop_processing = pyqtSignal()
    toggle_landmarks = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        self.landmarks_check = QCheckBox("Показывать ключевые точки")
        self.start_btn = QPushButton("Start")
        
        layout = QHBoxLayout(self)  # Указываем parent для layout
        layout.addWidget(self.landmarks_check)
        layout.addWidget(self.start_btn)
        
        self.landmarks_check.setChecked(True)
        self.landmarks_check.stateChanged.connect(
            lambda state: self.toggle_landmarks.emit(state == 2)
        )
        self.start_btn.clicked.connect(self._on_start_stop)
        
    def _on_start_stop(self):
        if self.start_btn.text() == "Start":
            self.start_processing.emit()
            self.start_btn.setText("Stop")
        else:
            self.stop_processing.emit()
            self.start_btn.setText("Start")