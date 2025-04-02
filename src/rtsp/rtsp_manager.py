from PyQt6.QtWidgets import QDialog, QVBoxLayout, QMessageBox
from .rtsp_table import RtspTable
from .rtsp_controls import RtspControls
from .rtsp_edit_dialog import RtspEditDialog
from PyQt6.QtCore import pyqtSignal

class RtspManagerDialog(QDialog):
    list_updated = pyqtSignal()
    data_changed = pyqtSignal()
    
    def __init__(self, rtsp_storage, parent=None):
        super().__init__(parent)
        self.rtsp_storage = rtsp_storage
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Управление RTSP потоками")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
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
        """Открывает диалог добавления нового RTSP"""
        existing_names = set(self.rtsp_storage.get_all_rtsp().keys())
        dialog = RtspEditDialog(
            parent=self,
            existing_names=existing_names,
            is_edit_mode=False
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if self.rtsp_storage.add_rtsp(data['name'], data['url'], data['comment']):
                self.load_data()
                self.list_updated.emit()  # Отправляем сигнал об обновлении
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить RTSP поток")
    
    def edit_rtsp(self):
        """Открывает диалог редактирования выбранного RTSP"""
        selected = self.table.get_selected()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите RTSP поток для редактирования")
            return
            
        existing_names = set(self.rtsp_storage.get_all_rtsp().keys())
        existing_names.remove(selected['name'])
        
        dialog = RtspEditDialog(
            parent=self,
            existing_names=existing_names,
            is_edit_mode=True
        )
        
        dialog.name_input.setText(selected['name'])
        dialog.url_input.setText(selected['url'])
        dialog.comment_input.setPlainText(selected['comment'])
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if (self.rtsp_storage.remove_rtsp(selected['name']) and 
                self.rtsp_storage.add_rtsp(new_data['name'], new_data['url'], new_data['comment'])):
                self.load_data()
                self.list_updated.emit()  # Отправляем сигнал об обновлении
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить RTSP поток")