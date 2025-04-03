import os
import logging
from datetime import datetime

class AppLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(log_dir, f"{current_time}.txt")
        
        self.logger = logging.getLogger("PPE_Logger")
        self.logger.setLevel(logging.INFO)
        
        # Очистка предыдущих обработчиков
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Создаем обработчик с UTF-8 кодировкой
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(file_handler)

    @classmethod
    def get_logger(cls):
        return cls().logger