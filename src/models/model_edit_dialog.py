from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QTextEdit,
    QLineEdit, QDialogButtonBox, QMessageBox, QFileDialog, QPushButton
)
from PyQt6.QtCore import Qt
import os 

class ModelEditDialog(QDialog):
    def __init__(self, parent=None, is_edit_mode: bool = False):
        super().__init__(parent)
        self.is_edit_mode = is_edit_mode
        self.setup_ui()
        
    def setup_ui(self):
        self.setModal(True)
        self.setWindowTitle("Изменить модель" if self.is_edit_mode else "Добавить модель")
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.comment_input = QTextEdit()
        
        if not self.is_edit_mode:
            self.path_input = QLineEdit()
            self.path_input.setReadOnly(True)
            self.browse_btn = QPushButton("Обзор")
            form.addRow("Путь к модели:", self.path_input)
            form.addRow("", self.browse_btn)
            self.browse_btn.clicked.connect(self._browse_folder)
        
        form.addRow("Название модели:", self.name_input)
        form.addRow("Комментарий:", self.comment_input)
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        
        self.ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Сохранить изменения" if self.is_edit_mode else "Добавить модель")
        
        self.buttons.accepted.connect(self._validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addLayout(form)
        layout.addWidget(self.buttons)
        self.setLayout(layout)
        
    def _browse_folder(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с моделью (.pt и .yaml файлы)",
            desktop,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        )
        
        if folder_path:
            self.path_input.setText(folder_path)
            
    def _validate_and_accept(self):
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название модели")
            return
            
        if not self.is_edit_mode:
            path = self.path_input.text().strip()
            if not path:
                QMessageBox.warning(self, "Ошибка", "Укажите путь к модели")
                return
                
            if not os.path.isdir(path):
                QMessageBox.warning(self, "Ошибка", "Укажите путь к папке с моделью, а не к файлу")
                return
                
            try:
                files = os.listdir(path)
                pt_files = [f for f in files if f.lower().endswith('.pt')]
                yaml_files = [f for f in files if f.lower().endswith('.yaml')]
                
                if not pt_files or not yaml_files:
                    missing = []
                    if not pt_files: missing.append(".pt файл")
                    if not yaml_files: missing.append(".yaml файл")
                    QMessageBox.warning(self, "Неполная модель", 
                                    f"Отсутствуют: {', '.join(missing)}")
                    return
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось проверить файлы модели: {str(e)}")
                return
        
        self.accept()
        
    def get_model_data(self):
        data = {
            'name': self.name_input.text().strip(),
            'comment': self.comment_input.toPlainText().strip()
        }
        if not self.is_edit_mode:
            data['path'] = self.path_input.text().strip()
        return data
        
    def set_model_data(self, model_data):
        self.name_input.setText(model_data.get('name', ''))
        self.comment_input.setPlainText(model_data.get('comment', ''))