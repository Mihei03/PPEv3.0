from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from src.config import Config
import os
from glob import glob
from utils.logger import AppLogger

class ModelHandler(QObject):
    model_loaded = pyqtSignal(str, dict)  # Сигнал с именем модели и информацией
    model_loading = pyqtSignal(str)
    
    def __init__(self, parent=None): 
        super().__init__(parent)
        self.logger = AppLogger.get_logger()
        
    def refresh_models_list(self):
        """Возвращает список доступных моделей с проверкой директории"""
        if not os.path.exists(Config.MODELS_ROOT):
            os.makedirs(Config.MODELS_ROOT, exist_ok=True)
            return []
            
        models = Config.get_available_models()
        return sorted(models.keys())  # Сортируем по алфавиту
        
    def load_model(self, model_name):
        """Загрузка модели с проверками и сигналами"""
        if not model_name or model_name == "Нет доступных моделей":
            return False
            
        try:
            self.model_loading.emit(model_name)
            models = Config.get_available_models()
            
            if model_name not in models:
                self.logger.error(f"Модель {model_name} не найдена")
                raise ValueError(f"Модель {model_name} не найдена")
                
            model_info = models[model_name]
            
            # Добавляем имена классов в model_info
            if 'ppe' in model_name.lower():  # или другой идентификатор вашей модели
                model_info['class_names'] = ['glove', 'helmet', 'pants', 'vest']
            
            # Проверка существования файлов модели
            if not os.path.exists(model_info['pt_file']) or not os.path.exists(model_info['yaml_file']):
                self.logger.error(f"Файлы модели {model_name} не найдена")
                raise FileNotFoundError(f"Файлы модели {model_name} не найдены")
            
            self.model_loaded.emit(model_name, model_info)
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {str(e)}")
            return False