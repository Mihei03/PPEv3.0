from PyQt6.QtWidgets import QComboBox, QPushButton, QHBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal

class ModelSelector(QWidget):
    model_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):  # Изменено на необязательный parent
        super().__init__(parent)
        self.current_model = None
        self._setup_ui()
        
    def _setup_ui(self):
        self.combo = QComboBox()
        self.load_btn = QPushButton("Активировать модель")
        
        layout = QHBoxLayout()
        layout.addWidget(self.combo)
        layout.addWidget(self.load_btn)
        self.setLayout(layout)
        
        self.load_btn.clicked.connect(self._activate_model)
        self.combo.currentTextChanged.connect(self._on_model_changed)
        
    def refresh_models(self, models):
        """Обновление списка моделей с выделением первой"""
        self.combo.clear()
        if models:
            self.combo.addItems(models)
            self.combo.setCurrentIndex(0)  # Автовыбор первой модели
            self.current_model = models[0]
        else:
            self.combo.addItem("Нет доступных моделей")
            self.current_model = None
        
    def _on_model_changed(self, model_name):
        self.current_model = model_name
        
    def _activate_model(self):
        if self.current_model and self.current_model != "Нет доступных моделей":
            self.model_selected.emit(self.current_model)