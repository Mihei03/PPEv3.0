from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from src.config import Config
import os
from glob import glob
import shutil

class ModelHandler(QObject):
    model_loaded = pyqtSignal(dict)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
    def refresh_models_list(self):
        """Возвращает список доступных моделей"""
        models = Config.get_available_models()
        return list(models.keys()) if models else []
        
    def load_model(self, model_name):
        """Загружает выбранную модель"""
        try:
            if model_name == "Загрузить другую модель...":
                model_dir = QFileDialog.getExistingDirectory(
                    self.parent, 
                    "Выберите папку с моделью",
                    "",
                    QFileDialog.Option.ShowDirsOnly
                )
                
                if not model_dir:
                    return None
                    
                pt_files = glob(os.path.join(model_dir, "*.pt"))
                yaml_files = glob(os.path.join(model_dir, "data.yaml"))
                
                if not pt_files or not yaml_files:
                    raise ValueError("Папка должна содержать .pt файл и data.yaml")
                    
                model_name = os.path.basename(model_dir)
                target_dir = os.path.join(Config.MODELS_ROOT, model_name)
                
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    shutil.copy(pt_files[0], os.path.join(target_dir, os.path.basename(pt_files[0])))
                    shutil.copy(yaml_files[0], os.path.join(target_dir, "data.yaml"))
                
                model_info = {
                    'path': target_dir,
                    'pt_file': os.path.join(target_dir, os.path.basename(pt_files[0])),
                    'yaml_file': os.path.join(target_dir, "data.yaml")
                }
            else:
                models = Config.get_available_models()
                model_info = models.get(model_name)
                if not model_info:
                    raise FileNotFoundError("Модель не найдена")
            
            self.model_loaded.emit(model_info)
            return model_info
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Ошибка", f"Не удалось загрузить модель:\n{str(e)}")
            return None