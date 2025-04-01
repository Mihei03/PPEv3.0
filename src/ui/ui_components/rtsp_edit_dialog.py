from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, 
    QLineEdit, QTextEdit, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt
from src.detection.rtsp_validator import RtspValidator


class RtspEditDialog(QDialog):
    def __init__(self, parent=None, existing_names=None, is_edit_mode: bool = False):
        super().__init__(parent)
        self.existing_names = existing_names or set()
        self.is_edit_mode = is_edit_mode  
        self.setup_ui()

    def setup_ui(self):
        """Настраивает интерфейс диалогового окна"""
        # Устанавливаем заголовок окна в зависимости от режима
        title = "Изменить RTSP поток" if self.is_edit_mode else "Добавить новый RTSP поток"
        self.setWindowTitle(title)
        self.setModal(True)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        # Поле для названия
        self.name_input = QLineEdit()
        name_label = "Название:"
        name_tooltip = ("Редактирование существующего названия RTSP потока" 
                       if self.is_edit_mode 
                       else "Введите уникальное название для нового RTSP потока")
        self.name_input.setToolTip(name_tooltip)
        form.addRow(name_label, self.name_input)
        
        # Поле для URL
        self.url_input = QLineEdit()
        url_tooltip = ("Редактирование RTSP URL. Формат: rtsp://[user:pass@]host[:port]/path"
                      if self.is_edit_mode 
                      else "Введите RTSP URL. Формат: rtsp://[user:pass@]host[:port]/path")
        self.url_input.setToolTip(url_tooltip)
        form.addRow("URL:", self.url_input)
        
        # Поле для комментария
        self.comment_input = QTextEdit()
        comment_tooltip = ("Редактирование комментария" 
                          if self.is_edit_mode 
                          else "Добавьте комментарий (необязательно)")
        self.comment_input.setToolTip(comment_tooltip)
        form.addRow("Комментарий:", self.comment_input)
        
        # Кнопки OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        
        # Меняем текст кнопки OK в зависимости от режима
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setText("Сохранить изменения" if self.is_edit_mode else "Добавить поток")
        
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _validate_and_accept(self):
        """Проверка с использованием полной валидации RTSP"""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
            return
            
        # Полная проверка URL
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
            
        self.accept()

    def get_data(self):
        """Возвращает введённые данные в виде словаря"""
        return {
            "name": self.name_input.text().strip(),
            "url": self.url_input.text().strip(),
            "comment": self.comment_input.toPlainText().strip()
        }