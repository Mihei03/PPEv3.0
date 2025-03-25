import os
import yaml
from glob import glob

class Config:
    CAMERA_INDEX = 0
    MODELS_ROOT = os.path.abspath(os.path.join("data", "models"))
    
    @staticmethod
    def get_available_models():
        """Находит все валидные модели в подпапках"""
        models = {}
        if not os.path.exists(Config.MODELS_ROOT):
            return models
            
        for model_dir in os.listdir(Config.MODELS_ROOT):
            model_path = os.path.join(Config.MODELS_ROOT, model_dir)
            if os.path.isdir(model_path):
                # Ищем любой .pt файл и data.yaml
                pt_files = glob(os.path.join(model_path, "*.pt"))
                yaml_files = glob(os.path.join(model_path, "data.yaml"))
                
                if pt_files and yaml_files:
                    models[model_dir] = {
                        'path': model_path,
                        'pt_file': pt_files[0],
                        'yaml_file': yaml_files[0]
                    }
        return models