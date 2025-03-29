import json
import re
from pathlib import Path
from typing import Dict
from utils.logger import AppLogger

class RtspStorage:
    RTSP_REGEX = r'^rtsp://(?:[^:@\s]+:[^@\s]+@)?[a-zA-Z0-9.-]+(?::\d+)?(?:/[^\s]*)?$'
    
    def __init__(self, storage_path: str = None):
        self.logger = AppLogger.get_logger()
        
        # Если путь не указан, используем "config/rtsp_config.json" (в папке config рядом с программой)
        default_path = "data/config/rtsp_config.json"
        
        # Если storage_path не передан, используем default_path
        self.storage_file = Path(storage_path) if storage_path else Path(default_path)
        
        # Создаем папку, если ее нет
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Создаем файл, если его нет
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Создает файл хранилища, если он не существует"""
        if not self.storage_file.exists():
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)
            self.logger.info(f"Создан новый файл хранилища: {self.storage_file}")

    def _validate_rtsp_url(self, url: str) -> bool:
        """Проверяет корректность RTSP ссылки"""
        if not re.match(self.RTSP_REGEX, url, re.IGNORECASE):
            return False
        return True

    def add_rtsp(self, name: str, url: str, comment: str = "") -> bool:
        try:
            # Проверяем URL перед добавлением
            if not self._validate_rtsp_url(url):
                self.logger.error(f"Некорректный RTSP URL: {url}")
                return False
                
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            if name in data:
                self.logger.error(f"RTSP с именем '{name}' уже существует")
                return False
                
            data[name] = {
                "url": url,
                "comment": comment
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка добавления RTSP: {e}")
            return False

    def get_all_rtsp(self) -> Dict[str, dict]:
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка чтения RTSP: {e}")
            return {}

    def remove_rtsp(self, name: str) -> bool:
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            if name not in data:
                return False
                
            del data[name]
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            self.logger.error(f"Ошибка удаления RTSP: {e}")
            return False