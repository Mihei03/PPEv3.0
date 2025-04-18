from PyQt6.QtWidgets import QDialog, QVBoxLayout, QMessageBox

from models.model_storage import ModelStorage
from .rtsp_table import RtspTable
from .rtsp_controls import RtspControls
from .rtsp_edit_dialog import RtspEditDialog
from PyQt6.QtCore import pyqtSignal

class RtspManagerDialog(QDialog):
    list_updated = pyqtSignal()
    data_changed = pyqtSignal()
    
    def __init__(self, rtsp_storage, model_handler=None, parent=None):
        super().__init__(parent)
        self.rtsp_storage = rtsp_storage
        self.model_handler = model_handler 
        self.model_storage = ModelStorage()
        self.parent_window = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Управление RTSP потоками")
        self.setModal(True)
        self.setMinimumSize(1000, 600)
        
        layout = QVBoxLayout()
        
        # Таблица
        self.table = RtspTable()
        
        # Панель управления
        self.controls = RtspControls(self)
        
        layout.addWidget(self.table)
        layout.addWidget(self.controls)
        self.setLayout(layout)
        
        self.load_data()
        
    def load_data(self):
        """Загружает данные из хранилища и обновляет таблицу"""
        rtsp_list = self.rtsp_storage.get_all_rtsp()
        self.table.populate(rtsp_list)
    
    def add_rtsp(self):
        existing_names = set(self.rtsp_storage.get_all_rtsp().keys())
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAa")
        dialog = RtspEditDialog(
            parent=self,
            existing_names=existing_names,
            is_edit_mode=False,
            available_models=self.model_storage.get_all_models() if self.model_handler else []
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if self.rtsp_storage.add_rtsp(data['name'], data['url'], data['comment'], data['model']):
                self.load_data()
                self.list_updated.emit()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить RTSP поток")
    
    def edit_rtsp(self):
        selected = self.table.get_selected()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите RTSP поток для редактирования")
            return
            
        existing_names = set(self.rtsp_storage.get_all_rtsp().keys())
        existing_names.remove(selected['name'])
        
        dialog = RtspEditDialog(
            parent=self,
            existing_names=existing_names,
            is_edit_mode=True,
            available_models=self.model_storage.get_all_models() if self.model_handler else []
        )
        
        dialog.name_input.setText(selected['name'])
        dialog.url_input.setText(selected['url'])
        dialog.comment_input.setPlainText(selected['comment'])
        if 'model' in selected:
            dialog.set_model(selected['model'])
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if (self.rtsp_storage.remove_rtsp(selected['name']) and 
                self.rtsp_storage.add_rtsp(new_data['name'], new_data['url'], new_data['comment'], new_data['model'])):
                self.load_data()
                self.list_updated.emit()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить RTSP поток")