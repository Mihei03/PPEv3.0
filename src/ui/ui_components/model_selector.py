from PyQt6.QtWidgets import QComboBox, QPushButton, QHBoxLayout, QWidget, QLabel, QMessageBox
from PyQt6.QtCore import pyqtSignal

class ModelSelector(QWidget):
    model_selected = pyqtSignal(str)
    load_model_requested = pyqtSignal()

    def __init__(self, parent=None):  # Изменено на необязательный parent
        super().__init__(parent)
        self.current_model = None
        self._setup_ui()
        
    def _setup_ui(self):
        # Добавляем label перед комбобоксом
        layout = QHBoxLayout()
    
        # Явно добавляем QLabel
        self.model_label = QLabel("Модели:")
        self.model_label.setObjectName("modelLabel")
        layout.addWidget(self.model_label)

        self.combo = QComboBox()
        self.load_btn = QPushButton("Активировать модель")
        self.add_btn = QPushButton("Добавить модель")
        self.add_btn.setToolTip("Загрузить модель из папки с .pt и .yaml файлами")

        layout = QHBoxLayout()
        layout.addWidget(self.model_label, stretch=1)
        layout.addWidget(self.combo, stretch=2)
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
        """Обновление списка моделей с сбросом состояния"""
        self.combo.clear()
        if models:
            self.combo.addItems(models)
            self.combo.setCurrentIndex(0)
            self.current_model = models[0]
        else:
            self.combo.addItem("Нет доступных моделей")
            self.current_model = None
        
        # Просто эмитируем сигнал, обработка будет в MainWindow
        self._on_model_changed(self.combo.currentText())
        
    def _on_model_changed(self, model_name):
        """При любом изменении модели делаем кнопку серой"""
        self.current_model = model_name
        if model_name == "Нет доступных моделей":
            self.current_model = None
        
        # Находим ControlPanel через родительскую цепочку
        widget = self
        while widget:
            if hasattr(widget, 'control_panel'):
                widget.control_panel.set_start_button_enabled(False)
                break
            widget = widget.parent()
        
        self.model_selected.emit(model_name if model_name != "Нет доступных моделей" else "")

    def set_model_handler(self, handler):
        self.model_handler = handler
        
    def _activate_model(self):
        """Просто эмитируем сигнал выбора модели"""
        if self.current_model and self.current_model != "Нет доступных моделей":
            self.model_selected.emit(self.current_model)
        else:
            QMessageBox.warning(self, "Ошибка", "Выберите модель из списка")
    
    def setEnabled(self, enabled):
        """Переопределяем для правильного обновления стилей"""
        super().setEnabled(enabled)
        for child in self.findChildren(QWidget):
            child.setEnabled(enabled)
            child.style().unpolish(child)
            child.style().polish(child)