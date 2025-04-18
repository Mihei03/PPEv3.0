from PyQt6.QtWidgets import QDialog, QVBoxLayout, QMessageBox

from core.utils.logger import AppLogger
from models.model_storage import ModelStorage
from .model_table import ModelTable
from .model_controls import ModelControls
from .model_edit_dialog import ModelEditDialog
from PyQt6.QtCore import pyqtSignal
import os

class ModelManagerDialog(QDialog):
    models_updated = pyqtSignal()
    
    def __init__(self, model_handler, parent=None):
        super().__init__(parent)
        self.model_handler = model_handler
        self.model_storage = ModelStorage()
        self.logger = AppLogger.get_logger()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Управление моделями")
        self.setModal(True)
        self.setMinimumSize(800, 500)
        
        layout = QVBoxLayout()
        
        # Таблица
        self.table = ModelTable()
        
        # Панель управления
        self.controls = ModelControls(self)
        
        layout.addWidget(self.table)
        layout.addWidget(self.controls)
        self.setLayout(layout)
        
        self.load_data()
        
    def load_data(self):
        """Загружает данные моделей и обновляет таблицу"""
        # models = self.model_handler.get_models_info()
        models = self.model_storage.get_all_models()
        self.logger.info(models)
        
        self.table.populate(models)
        # Принудительно обновляем сортировку
        self.table.sortItems(self.table._last_sorted_column, self.table._sort_order)
    
    def add_model(self):
        dialog = ModelEditDialog(parent=self, is_edit_mode=False)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            model_data = dialog.get_model_data()
            if not model_data['name']:
                QMessageBox.warning(self, "Ошибка", "Название модели не может быть пустым")
                return
                
            # Передаем и путь к папке, и желаемое имя модели
            if self.model_handler.add_model_from_folder(
                folder_path=model_data['path'],
                model_name=model_data['name']
            ):

                self.model_storage.add_model(model_data['name'], model_data['comment'])

                self.load_data()
                self.models_updated.emit()
    
    def remove_model(self):
        selected = self.table.get_selected()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите модель для удаления")
            return
            
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            f"Вы уверены, что хотите удалить модель '{selected['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.model_handler.remove_model(selected['name']):
                
                self.model_storage.remove_model(selected['name'])

                self.load_data()
                self.models_updated.emit()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить модель")
    
    def edit_model(self):
        selected = self.table.get_selected()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите модель для редактирования")
            return
            
        dialog = ModelEditDialog(parent=self, is_edit_mode=True)
        dialog.set_model_data(selected)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_model_data()
            
            #Если имя изменилось - переименовываем модель
            if new_data['name'] != selected['name']: 
                if not self.model_handler.rename_model(selected['name'], new_data['name']):
                    QMessageBox.warning(self, "Ошибка", "Не удалось переименовать модель")
                    return
                
            self.model_storage.update_model(selected['name'], new_data)
            
            self.load_data()
            self.models_updated.emit()