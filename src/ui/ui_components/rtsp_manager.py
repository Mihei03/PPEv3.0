from PyQt6.QtWidgets import QDialog, QVBoxLayout
from .rtsp_table import RtspTable
from .rtsp_controls import RtspControls

class RtspManagerDialog(QDialog):
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