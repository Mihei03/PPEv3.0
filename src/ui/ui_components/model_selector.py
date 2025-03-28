from PyQt6.QtWidgets import QComboBox, QPushButton, QHBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal

class ModelSelector(QWidget):
    model_selected = pyqtSignal(str)
    load_model_requested = pyqtSignal()

    def __init__(self, parent=None):  # Изменено на необязательный parent
        super().__init__(parent)
        self.current_model = None
        self._setup_ui()
        
    def _setup_ui(self):
        self.combo = QComboBox()
        self.load_btn = QPushButton("Активировать модель")
        self.add_btn = QPushButton("Добавить модель")
        self.add_btn.setToolTip("Загрузить модель из папки с .pt и .yaml файлами")

        layout = QHBoxLayout()
        layout.addWidget(self.combo, stretch=4)
        layout.addWidget(self.load_btn, stretch=1)
        layout.addWidget(self.add_btn, stretch=1)
        self.setLayout(layout)

        self.load_btn.clicked.connect(self._activate_model)
        self.add_btn.clicked.connect(self._add_model)
        self.combo.currentTextChanged.connect(self._on_model_changed)

    def _add_model(self):
        """Инициирует процесс добавления модели"""
        self.load_model_requested.emit()

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