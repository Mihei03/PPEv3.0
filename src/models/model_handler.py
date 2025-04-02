from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import os
import shutil
import yaml
from src.config import Config
from utils.logger import AppLogger

class ModelHandler(QObject):
    model_loaded = pyqtSignal(str, dict)
    model_loading = pyqtSignal(str)
    models_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__()
        self.logger = AppLogger.get_logger()
        self._current_model = None
        self._model_activated = False
        self.yolo = None

    def current_model(self):
        return self._current_model
    
    def is_model_loaded(self):
        return self._model_activated and bool(self._current_model)
    
    def refresh_models_list(self):
        if not os.path.exists(Config.MODELS_ROOT):
            os.makedirs(Config.MODELS_ROOT, exist_ok=True)
            return []
            
        return sorted(Config.get_available_models().keys())
    
    def rename_model(self, old_name, new_name):
        """Переименовывает модель"""
        try:
            if not new_name or new_name == old_name:
                return False
                
            old_dir = os.path.join(Config.MODELS_ROOT, old_name)
            new_dir = os.path.join(Config.MODELS_ROOT, new_name)
            
            if os.path.exists(new_dir):
                return False
                
            os.rename(old_dir, new_dir)
            self.models_updated.emit()
            return True
        except Exception as e:
            self.logger.error(f"Ошибка переименования модели: {str(e)}")
            return False
    
    def get_models_info(self):
        """Возвращает информацию о моделях с комментариями"""
        models = Config.get_available_models()
        result = {}
        for name, info in models.items():
            comment_file = os.path.join(Config.MODELS_ROOT, name, "comment.txt")
            comment = ""
            if os.path.exists(comment_file):
                try:
                    with open(comment_file, 'r', encoding='utf-8') as f:
                        comment = f.read().strip()
                except:
                    comment = ""
            result[name] = {
                'path': info['pt_file'],
                'comment': comment
            }
        return result

    def save_model_comment(self, model_name, comment):
        """Сохраняет комментарий к модели"""
        try:
            model_dir = os.path.join(Config.MODELS_ROOT, model_name)
            os.makedirs(model_dir, exist_ok=True)
            with open(os.path.join(model_dir, "comment.txt"), 'w', encoding='utf-8') as f:
                f.write(comment)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения комментария: {str(e)}")
            return False

    def remove_model(self, model_name):
        """Удаляет модель"""
        try:
            model_dir = os.path.join(Config.MODELS_ROOT, model_name)
            if os.path.exists(model_dir):
                shutil.rmtree(model_dir)
                self.models_updated.emit()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка удаления модели: {str(e)}")
            return False
        
    def set_yolo_detector(self, yolo_detector):
        """Явная установка YOLO детектора с проверкой"""
        if yolo_detector is None:
            self.logger.error("Попытка установить None как YOLO детектор!")
            return
            
        self.yolo = yolo_detector
        self.logger.info("YOLO детектор успешно установлен в ModelHandler")
        
        # Проверка возможности загрузки модели
        if hasattr(self._current_model, 'model_name'):
            self.logger.info(f"Повторная попытка загрузки модели {self._current_model}")
            self.load_model(self._current_model)

    def load_model(self, model_name):
        if not model_name or model_name == "Нет доступных моделей":
            self.logger.warning("Попытка загрузить пустую модель")
            return False
            
        if self.yolo is None:
            self.logger.error("YOLO детектор не инициализирован!")
            return False
            
        try:
            self.model_loading.emit(model_name)
            models = Config.get_available_models()
            
            if model_name not in models:
                error_msg = f"Модель {model_name} не найдена"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
                
            model_info = models[model_name]
            
            # Проверка файлов модели
            if not os.path.exists(model_info['pt_file']):
                raise FileNotFoundError(f"Файл модели {model_info['pt_file']} не найден")
                
            if not os.path.exists(model_info['yaml_file']):
                raise FileNotFoundError(f"Конфиг {model_info['yaml_file']} не найден")
            
            # Загрузка модели через YOLO детектор
            if self.yolo.load_model(model_name, model_info):
                self._current_model = model_name
                self._model_activated = True
                self.model_loaded.emit(model_name, model_info)
                self.logger.info(f"Модель {model_name} успешно загружена")
                return True
                
            self.logger.error(f"Не удалось загрузить модель {model_name}")
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели {model_name}: {str(e)}", exc_info=True)
            self._model_activated = False
            return False

    def is_model_activated(self):
        return self._model_activated and bool(self._current_model)

    def add_model_from_folder(self, folder_path=None, model_name=None):
        """Добавляет модель из папки с указанным именем"""
        try:
            if folder_path is None:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                folder_path = QFileDialog.getExistingDirectory(
                    None,
                    "Выберите папку с моделью (.pt и .yaml файлы)",
                    desktop,
                    QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
                )

                if not folder_path:
                    return False

            # Проверка файлов модели
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

            # Создаем папку с указанным именем модели
            target_dir = os.path.join(Config.MODELS_ROOT, model_name)
            os.makedirs(target_dir, exist_ok=True)

            # Копируем файлы модели
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
        try:
            with open(model_info['yaml_file'], 'r') as f:
                data = yaml.safe_load(f)
                return data.get('names', [])
        except Exception:
            if 'ppe' in model_name.lower():
                return ['glove', 'helmet', 'pants', 'vest']
            return []