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
        self.add_btn.clicked.connect(self.add_rtsp)
        
        self.edit_btn = QPushButton("Изменить")
        self.edit_btn.clicked.connect(self.edit_rtsp)
        
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_rtsp)
        
        layout.addWidget(self.add_btn)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.delete_btn)
        self.setLayout(layout)
    
    def add_rtsp(self):
        existing_names = set(self.manager.rtsp_storage.get_all_rtsp().keys())
        dialog = RtspEditDialog(self, existing_names)
        if dialog.exec():
            data = dialog.get_data()
            if self.manager.rtsp_storage.add_rtsp(data["name"], data["url"], data["comment"]):
                self.manager.load_data()
    
    def edit_rtsp(self):
        selected = self.manager.table.currentRow()
        if selected >= 0:
            name_item = self.manager.table.item(selected, 1)
            if not name_item:
                return
                
            old_name = name_item.text()
            rtsp_data = self.manager.rtsp_storage.get_all_rtsp().get(old_name, {})
            
            existing_names = set(self.manager.rtsp_storage.get_all_rtsp().keys())
            existing_names.remove(old_name)  # Исключаем текущее имя из проверки
            
            dialog = RtspEditDialog(self, existing_names)
            dialog.name_input.setText(old_name)
            dialog.url_input.setText(rtsp_data.get("url", ""))
            dialog.comment_input.setPlainText(rtsp_data.get("comment", ""))
            
            if dialog.exec():
                new_data = dialog.get_data()
                self.manager.rtsp_storage.remove_rtsp(old_name)
                if self.manager.rtsp_storage.add_rtsp(new_data["name"], new_data["url"], new_data["comment"]):
                    self.manager.load_data()
    
    def delete_rtsp(self):
        selected = self.manager.table.currentRow()
        if selected >= 0:
            name_item = self.manager.table.item(selected, 1)
            if not name_item:
                return
                
            name = name_item.text()
            reply = QMessageBox.question(
                self, 
                "Подтверждение", 
                f"Вы уверены, что хотите удалить '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if self.manager.rtsp_storage.remove_rtsp(name):
                    self.manager.load_data()