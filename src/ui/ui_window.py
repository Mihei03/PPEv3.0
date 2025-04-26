from PyQt6.QtWidgets import QMainWindow, QMessageBox, QToolBar
from .builders.ui_builder import UIBuilder
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QUrl, QDir
from PyQt6.QtGui import QDesktopServices
import os

class MainWindowUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_builder = UIBuilder(self)
        self.ui_builder.build_ui()
        self.setMinimumSize(1200, 900)
        
        self.toolbar = QToolBar("Панель инструментов")
        self.addToolBar(self.toolbar)
        
        # Получаем абсолютный путь к директории с документацией
        self.docs_dir = os.path.join(QDir.currentPath(), "data", "docs")
        
        # Добавляем кнопку "Руководство пользователя"
        self.user_manual_action = QAction("Руководство пользователя", self)
        self.user_manual_action.triggered.connect(self.open_user_manual)
        self.toolbar.addAction(self.user_manual_action)
        
        # Добавляем кнопку "О программе"
        self.about_action = QAction("О программе", self)
        self.about_action.triggered.connect(self.open_about)
        self.toolbar.addAction(self.about_action)
        
        # Делаем компоненты доступными напрямую
        self.model_panel = self.ui_builder.model_panel
        self.control_panel = self.ui_builder.control_panel
        self.status_bar = self.ui_builder.status_bar
        self.video_display = self.ui_builder.video_display
    
    def get_doc_path(self, filename):
        """Возвращает абсолютный путь к файлу документации"""
        return os.path.join(self.docs_dir, filename)
    
    def open_user_manual(self):
        """Открывает руководство пользователя в браузере"""
        manual_path = self.get_doc_path("user_manual.html")
        if os.path.exists(manual_path):
            url = QUrl.fromLocalFile(manual_path)
            QDesktopServices.openUrl(url)
        else:
            self.show_warning("Ошибка", "Файл руководства пользователя не найден")
    
    def open_about(self):
        """Открывает информацию о программе в браузере"""
        about_path = self.get_doc_path("about.html")
        if os.path.exists(about_path):
            url = QUrl.fromLocalFile(about_path)
            QDesktopServices.openUrl(url)
        else:
            self.show_warning("Ошибка", "Файл информации о программе не найден")
            
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