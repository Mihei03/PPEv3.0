import os

class Config:
    CAMERA_INDEX = 0
    MODELS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "PPEV3.0", "data", "models")
    RTSP_SETTINGS = {
        'timeout': 5000,       # Таймаут подключения (мс)
        'buffer_size': 1,      # Размер буфера кадров
        'reconnect_delay': 3,  # Задержка переподключения (сек)
        'max_fps': 30          # Максимальный FPS
    }
    @staticmethod
    def get_available_models():
        """Возвращает доступные модели"""
        models = {}
        if not os.path.exists(Config.MODELS_ROOT):
            return models
            
        for model_dir in os.listdir(Config.MODELS_ROOT):
            model_path = os.path.join(Config.MODELS_ROOT, model_dir)
            if os.path.isdir(model_path):
                pt_files = [f for f in os.listdir(model_path) if f.endswith('.pt')]
                yaml_files = [f for f in os.listdir(model_path) if f.endswith('.yaml')]
                
                if pt_files and yaml_files:
                    models[model_dir] = {
                        'pt_file': os.path.join(model_path, pt_files[0]),
                        'yaml_file': os.path.join(model_path, yaml_files[0])
                    }
        return models