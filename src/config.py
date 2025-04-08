import os
import sys
from pathlib import Path

class Config:
    # Определяем базовый путь (корень проекта PPEv3.0)
    if getattr(sys, 'frozen', False):
        # Если приложение собрано в exe (например, PyInstaller)
        BASE_DIR = Path(sys.executable).parent
    else:
        # При обычном запуске Python - используем абсолютный путь к src и поднимаемся на один уровень вверх
        BASE_DIR = Path(__file__).absolute().parent.parent  # Переходим из src/config.py в PPEv3.0/

    # Папка с моделями относительно корня проекта
    MODELS_DIR = BASE_DIR / "data" / "models"
    
    # Для обратной совместимости
    MODELS_ROOT = MODELS_DIR
    
    CAMERA_INDEX = 0
    RTSP_SETTINGS = {
        'timeout': 5000,
        'buffer_size': 1,
        'reconnect_delay': 3,
        'max_fps': 30
    }

    @staticmethod
    def get_available_models():
        """Возвращает доступные модели, создает папку если ее нет"""
        models = {}
        
        # Создаем папку если ее нет
        os.makedirs(Config.MODELS_DIR, exist_ok=True)
        
        for model_dir in os.listdir(Config.MODELS_DIR):
            model_path = os.path.join(Config.MODELS_DIR, model_dir)
            if os.path.isdir(model_path):
                pt_files = [f for f in os.listdir(model_path) if f.endswith('.pt')]
                yaml_files = [f for f in os.listdir(model_path) if f.endswith('.yaml')]
                
                if pt_files and yaml_files:
                    models[model_dir] = {
                        'pt_file': os.path.join(model_path, pt_files[0]),
                        'yaml_file': os.path.join(model_path, yaml_files[0])
                    }
        return models