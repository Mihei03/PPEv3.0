from PyQt6.QtWidgets import QMainWindow, QMessageBox
from .builders.ui_builder import UIBuilder

class MainWindowUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_builder = UIBuilder(self)
        self.ui_builder.build_ui()
        self.setMinimumSize(1200, 900)
        
        # Делаем компоненты доступными напрямую
        self.model_panel = self.ui_builder.model_panel
        self.control_panel = self.ui_builder.control_panel
        self.status_bar = self.ui_builder.status_bar
        self.video_display = self.ui_builder.video_display
        
    def show_message(self, message, timeout=0):
        """Делегируем вызов статус бару"""
        self.status_bar.show_message(message, timeout)
    
    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)
    
    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if hasattr(self, 'controller'):
            self.controller.cleanup()
        super().closeEvent(event)