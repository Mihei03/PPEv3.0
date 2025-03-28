import os
import yaml
from glob import glob

class Config:
    CAMERA_INDEX = 0
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    MODELS_ROOT = os.path.join(PROJECT_ROOT, "PPEV3.0", "data", "models")
    os.makedirs(MODELS_ROOT, exist_ok=True)
    
    @staticmethod
    def get_available_models():
        """Возвращает модели с проверкой файлов"""
        models = {}
        if not os.path.exists(Config.MODELS_ROOT):
            return models
            
        for model_dir in os.listdir(Config.MODELS_ROOT):
            model_path = os.path.join(Config.MODELS_ROOT, model_dir)
            if os.path.isdir(model_path):
                # Проверяем наличие обязательных файлов
                pt_files = [f for f in os.listdir(model_path) if f.endswith('.pt')]
                yaml_files = [f for f in os.listdir(model_path) if f.endswith('.yaml')]
                
                if pt_files and yaml_files:
                    models[model_dir] = {
                        'path': model_path,
                        'pt_file': os.path.join(model_path, pt_files[0]),
                        'yaml_file': os.path.join(model_path, yaml_files[0])
                    }
        return models