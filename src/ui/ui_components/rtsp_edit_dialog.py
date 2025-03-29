from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                            QLineEdit, QTextEdit, QDialogButtonBox, QMessageBox)
from PyQt6.QtCore import Qt
import re

class RtspEditDialog(QDialog):
    RTSP_REGEX = r'^rtsp://(?:[^:@\s]+:[^@\s]+@)?[a-zA-Z0-9.-]+(?::\d+)?(?:/[^\s]*)?$'
    
    def __init__(self, parent=None, existing_names=None):
        super().__init__(parent)
        self.existing_names = existing_names or set()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Добавить/Изменить RTSP")
        self.setModal(True)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.url_input = QLineEdit()
        self.comment_input = QTextEdit()
        
        form.addRow("Название:", self.name_input)
        form.addRow("URL:", self.url_input)
        form.addRow("Комментарий:", self.comment_input)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def _validate_rtsp_url(self, url: str) -> bool:
        """Проверяет корректность RTSP ссылки"""
        return bool(re.match(self.RTSP_REGEX, url, re.IGNORECASE))
    
    def _validate_and_accept(self):
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым")
            return
            
        if not url:
            QMessageBox.warning(self, "Ошибка", "URL не может быть пустым")
            return
            
        if not self._validate_rtsp_url(url):
            QMessageBox.warning(
                self, 
                "Ошибка", 
                "Неверный формат RTSP ссылки. Пример:\n"
                "rtsp://user:pass@host:port/path\n"
                "или rtsp://host/path"
            )
            self.url_input.setFocus()
            self.url_input.selectAll()
            return
            
        if name in self.existing_names:
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
        return {
            "name": self.name_input.text().strip(),
            "url": self.url_input.text().strip(),
            "comment": self.comment_input.toPlainText().strip()
        }