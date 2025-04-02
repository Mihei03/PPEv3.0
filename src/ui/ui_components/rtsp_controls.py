from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMessageBox
from .rtsp_edit_dialog import RtspEditDialog

class RtspControls(QWidget):
    def __init__(self, manager_dialog):
        super().__init__()
        self.manager = manager_dialog
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Изменить")
        self.remove_btn = QPushButton("Удалить")
        
        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.remove_btn.clicked.connect(self._on_remove)
        
        layout.addWidget(self.add_btn)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.remove_btn)
        self.setLayout(layout)
    
    def _on_add(self):
        """Обработчик кнопки Добавить"""
        existing_names = set(self.manager.rtsp_storage.get_all_rtsp().keys())
        dialog = RtspEditDialog(
            parent=self,
            existing_names=existing_names,
            is_edit_mode=False
        )
        
        if dialog.exec():
            data = dialog.get_data()
            if self.manager.rtsp_storage.add_rtsp(data["name"], data["url"], data["comment"]):
                self.manager.load_data()
                self.manager.data_changed.emit()  # Отправляем сигнал
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить RTSP поток")

    def _on_edit(self):
        """Обработчик кнопки Изменить"""
        selected = self.manager.table.get_selected()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите RTSP поток для редактирования")
            return
            
        existing_names = set(self.manager.rtsp_storage.get_all_rtsp().keys())
        existing_names.remove(selected['name'])
        
        dialog = RtspEditDialog(
            parent=self,
            existing_names=existing_names,
            is_edit_mode=True
        )
        
        dialog.name_input.setText(selected['name'])
        dialog.url_input.setText(selected['url'])
        dialog.comment_input.setPlainText(selected['comment'])
        
        if dialog.exec():
            new_data = dialog.get_data()
            if (self.manager.rtsp_storage.remove_rtsp(selected['name']) and 
                self.manager.rtsp_storage.add_rtsp(new_data["name"], new_data["url"], new_data["comment"])):
                self.manager.load_data()
                self.manager.data_changed.emit()  # Отправляем сигнал
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить RTSP поток")

    def _on_remove(self):
        """Обработчик кнопки Удалить"""
        selected = self.manager.table.get_selected()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите RTSP поток для удаления")
            return
            
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            f"Вы уверены, что хотите удалить '{selected['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.manager.rtsp_storage.remove_rtsp(selected['name']):
                self.manager.load_data()
                self.manager.data_changed.emit()  # Отправляем сигнал
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить RTSP поток")