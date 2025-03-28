from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from src.config import Config
import os
from glob import glob
from utils.logger import AppLogger
import shutil

class ModelHandler(QObject):
    model_loaded = pyqtSignal(str, dict)  # Сигнал с именем модели и информацией
    model_loading = pyqtSignal(str)
    models_updated = pyqtSignal()

    def __init__(self, parent=None): 
        super().__init__(parent)
        self.logger = AppLogger.get_logger()
        
    def refresh_models_list(self):
        """Возвращает список доступных моделей с проверкой директории"""
        if not os.path.exists(Config.MODELS_ROOT):
            os.makedirs(Config.MODELS_ROOT, exist_ok=True)
            return []
            
        models = Config.get_available_models()
        return sorted(models.keys())
        
    def load_model(self, model_name):
        """Загрузка выбранной модели"""
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
            model_info['class_names'] = self._get_class_names(model_name, model_info)
            
            if not os.path.exists(model_info['pt_file']) or not os.path.exists(model_info['yaml_file']):
                self.logger.error(f"Файлы модели {model_name} не найдены")
                raise FileNotFoundError(f"Файлы модели {model_name} не найдены")
            
            self.model_loaded.emit(model_name, model_info)
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {str(e)}")
            return False

    def add_model_from_folder(self):
        """Добавление модели через диалог выбора папки"""
        try:
            # Получаем путь к рабочему столу
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # Открываем диалог выбора папки с фильтрами
            folder_path = QFileDialog.getExistingDirectory(
                None,
                "Выберите папку с моделью (.pt и .yaml файлы)",
                desktop,
                QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
            )

            if not folder_path:
                return False

            # Проверяем файлы в папке
            files = os.listdir(folder_path)
            pt_files = [f for f in files if f.lower().endswith('.pt')]
            yaml_files = [f for f in files if f.lower().endswith('.yaml')]

            if not pt_files or not yaml_files:
                missing = []
                if not pt_files: missing.append(".pt файл")
                if not yaml_files: missing.append(".yaml файл")
                QMessageBox.warning(None, "Неполная модель", 
                                  f"Отсутствуют: {', '.join(missing)}")
                return False

            # Создаем папку для модели
            model_name = os.path.basename(folder_path)
            target_dir = os.path.join(Config.MODELS_ROOT, model_name)
            os.makedirs(target_dir, exist_ok=True)

            # Копируем файлы
            for file in pt_files + yaml_files:
                src = os.path.join(folder_path, file)
                dst = os.path.join(target_dir, file)
                shutil.copy2(src, dst)

            self.logger.info(f"Модель '{model_name}' успешно добавлена")
            self.models_updated.emit()
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {str(e)}")
            QMessageBox.critical(None, "Ошибка", 
                               f"Не удалось добавить модель:\n{str(e)}")
            return False
    
    def _get_class_names(self, model_name, model_info):
        """Получает имена классов из YAML файла или возвращает стандартные"""
        try:
            import yaml
            with open(model_info['yaml_file'], 'r') as f:
                data = yaml.safe_load(f)
                return data.get('names', [])
        except Exception:
            if 'ppe' in model_name.lower():
                return ['glove', 'helmet', 'pants', 'vest']
            return []