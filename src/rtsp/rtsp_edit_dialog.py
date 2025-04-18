from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QDialogButtonBox, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from core.utils.rtsp_validator import RtspValidator


class RtspEditDialog(QDialog):
    def __init__(self, parent=None, existing_names=None, is_edit_mode: bool = False, available_models=None):
        super().__init__(parent)
        self.existing_names = existing_names or set()
        self.is_edit_mode = is_edit_mode  
        self.available_models = available_models or []
        self.setup_ui()

    def setup_ui(self):
        """Настраивает интерфейс диалогового окна"""
        self.setModal(True)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        # Поле для названия
        self.name_input = QLineEdit()
        form.addRow("Название:", self.name_input)
        
        # Поле для URL
        self.url_input = QLineEdit()
        form.addRow("URL:", self.url_input)
        self.url_input.textChanged.connect(self._validate_url)

        # Поле для комментария
        self.comment_input = QTextEdit()
        form.addRow("Комментарий:", self.comment_input)
        
        # Комбобокс для выбора модели
        self.model_combo = QComboBox()
        form.addRow("Привязать модель:", self.model_combo)
        
        # Кнопки OK/Cancel
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
    
        self.ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.cancel_button = self.buttons.button(QDialogButtonBox.StandardButton.Cancel)
        self.ok_button.setText("Сохранить" if self.is_edit_mode else "Добавить")
        self.cancel_button.setText("Отмена")  # Устанавливаем русский текст
        
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addLayout(form)
        layout.addWidget(self.buttons)
        self.setLayout(layout)
        
        # Теперь обновляем модели после создания всех элементов UI
        self._update_models_combo()
        self._update_ui_for_mode()

    def _update_models_combo(self):
        """Обновляет список моделей в комбобоксе, проверяя их актуальность"""
        self.model_combo.clear()
        
        if self.available_models:
            for id, model_name, _ in self.available_models:
                self.model_combo.addItem(model_name, id)
        
        # Проверяем, создана ли уже кнопка ok_button
        if hasattr(self, 'ok_button'):
            if self.model_combo.count() == 0:
                self.model_combo.addItem("Нет доступных моделей", None)
                self.model_combo.setEnabled(False)
                self.ok_button.setEnabled(False)
            else:
                self.model_combo.setEnabled(True)
                self.ok_button.setEnabled(True)

    def _validate_url(self):
        url = self.url_input.text().strip()
        is_valid, _ = RtspValidator.validate_rtsp_url(url)
        
        self.url_input.setProperty("valid", is_valid)
        
        self.url_input.style().unpolish(self.url_input)
        self.url_input.style().polish(self.url_input)
        self.url_input.update()

    def _update_ui_for_mode(self):
        """Обновляет UI в зависимости от режима (добавление/редактирование)"""
        if self.is_edit_mode:
            self.setWindowTitle("Изменить RTSP поток")
            self.ok_button.setText("Сохранить изменения")
            self.name_input.setToolTip("Редактирование существующего названия RTSP потока")
            self.url_input.setToolTip("Редактирование RTSP URL. Формат: rtsp://[user:pass@]host[:port]/path")
            self.comment_input.setToolTip("Редактирование комментария")
            self.model_combo.setToolTip("Редактирование привязанной модели")
        else:
            self.setWindowTitle("Добавить новый RTSP поток")
            self.ok_button.setText("Добавить поток")
            self.name_input.setToolTip("Введите уникальное название для нового RTSP потока")
            self.url_input.setToolTip("Введите RTSP URL. Формат: rtsp://[user:pass@]host[:port]/path")
            self.comment_input.setToolTip("Добавьте комментарий (необязательно)")
            self.model_combo.setToolTip("Выберите модель для привязки к потоку")

    def _validate_and_accept(self):
        """Проверка с использованием полной валидации RTSP"""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
            return
            
        is_valid, error_msg = RtspValidator.validate_rtsp_url(url)
        if not is_valid:
            QMessageBox.warning(self, "Ошибка", error_msg)
            self.url_input.setFocus()
            self.url_input.selectAll()
            return
            
        if not self.is_edit_mode and name in self.existing_names:
            QMessageBox.warning(
                self, 
                "Ошибка", 
                "RTSP с таким именем уже существует. Пожалуйста, введите другое название."
            )
            self.name_input.setFocus()
            self.name_input.selectAll()
            return
            
        if not self.model_combo.currentData():
            QMessageBox.warning(self, "Ошибка", "Необходимо выбрать модель для RTSP потока")
            return
        
        self.accept()

    def get_data(self):
        """Возвращает введённые данные в виде словаря"""
        return {
            "name": self.name_input.text().strip(),
            "url": self.url_input.text().strip(),
            "comment": self.comment_input.toPlainText().strip(),
            "model": self.model_combo.currentData()
        }
    
    def set_model(self, model_name):
        """Устанавливает выбранную модель в комбобоксе"""
        index = self.model_combo.findData(model_name)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)