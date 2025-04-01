from PyQt6.QtWidgets import QComboBox, QPushButton, QHBoxLayout, QWidget, QLabel, QMessageBox
from PyQt6.QtCore import pyqtSignal

class ModelSelector(QWidget):
    model_selected = pyqtSignal(str)
    load_model_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_model = None
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout()
        self.model_label = QLabel("Модели:")
        self.model_label.setObjectName("modelLabel")
        
        self.combo = QComboBox()
        self.load_btn = QPushButton("Активировать модель")
        self.add_btn = QPushButton("Добавить модель")
        self.add_btn.setToolTip("Загрузить модель из папки с .pt и .yaml файлами")

        layout.addWidget(self.model_label, stretch=1)
        layout.addWidget(self.combo, stretch=2)
        layout.addWidget(self.load_btn, stretch=1)
        layout.addWidget(self.add_btn, stretch=1)
        self.setLayout(layout)

        self.load_btn.clicked.connect(self._activate_model)
        self.add_btn.clicked.connect(self._add_model)
        self.combo.currentTextChanged.connect(self._on_model_changed)

    def _add_model(self):
        self.load_model_requested.emit()

    def refresh_models(self, models):
        self.combo.clear()
        if not models:
            self.combo.addItem("Нет доступных моделей")
            self.current_model = None
            self._on_model_changed("")
            return
            
        self.combo.addItems(models)
        self.current_model = models[0]
        self._on_model_changed(models[0])
        
    def _on_model_changed(self, model_name):
        self.current_model = model_name if model_name != "Нет доступных моделей" else None
        self.model_selected.emit(self.current_model or "")

    def set_model_handler(self, handler):
        self.model_handler = handler
        
    def _activate_model(self):
        if not self.current_model:
            QMessageBox.warning(self, "Ошибка", "Выберите модель из списка")
            return
        self.model_selected.emit(self.current_model)
    
    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        for child in self.findChildren(QWidget):
            child.setEnabled(enabled)
            child.style().unpolish(child)
            child.style().polish(child)