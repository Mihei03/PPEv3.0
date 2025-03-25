from PyQt6.QtWidgets import QComboBox, QPushButton, QHBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal

class ModelSelector(QWidget):
    model_selected = pyqtSignal(str)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.combo = QComboBox()
        self.load_btn = QPushButton("Загрузить модель")
        
        layout = QHBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.load_btn)
        self.setLayout(layout)
        
        self.load_btn.clicked.connect(self._on_load_clicked)
        
    def refresh_models(self, models):
        self.combo.clear()
        if not models:
            self.combo.addItem("Нет доступных моделей")
            self.combo.setEnabled(False)
            self.load_btn.setEnabled(False)
        else:
            self.combo.addItems(models)
            self.combo.addItem("Загрузить другую модель...")
            self.combo.setEnabled(True)
            self.load_btn.setEnabled(True)
        
    def _on_load_clicked(self):
        selected = self.combo.currentText()
        if selected:
            self.model_selected.emit(selected)