import json
from pathlib import Path
from typing import Dict
from core.utils.logger import AppLogger
from core.utils.rtsp_validator import RtspValidator 


class RtspStorage:
    def __init__(self, storage_path: str = None):
        self.logger = AppLogger.get_logger()
        default_path = "data/config/rtsp_config.json"
        self.storage_file = Path(storage_path) if storage_path else Path(default_path)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Создаёт файл хранилища, если он не существует"""
        if not self.storage_file.exists():
            with open(self.storage_file, 'w') as f:
                json.dump({}, f)
            self.logger.info(f"Создан новый файл хранилища: {self.storage_file}")

    def add_rtsp(self, name: str, url: str, comment: str = "") -> bool:
        """Добавляет RTSP-поток в хранилище"""
        try:
            # Валидация через общий RtspValidator
            is_valid, error_msg = RtspValidator.validate_rtsp_url(url)
            if not is_valid:
                self.logger.error(f"Некорректный RTSP URL: {error_msg}")
                return False

            # Проверка уникальности URL
            existing_urls = {v['url'] for v in self.get_all_rtsp().values()}
            if url in existing_urls:
                self.logger.error(f"RTSP с URL '{url}' уже существует")
                return False
        
            with open(self.storage_file, 'r') as f:
                data = json.load(f)

            if name in data:
                self.logger.error(f"RTSP с именем '{name}' уже существует")
                return False

            data[name] = {"url": url, "comment": comment}

            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=4)
            return True

        except Exception as e:
            self.logger.error(f"Ошибка добавления RTSP: {e}")
            return False

    def get_all_rtsp(self) -> Dict[str, dict]:
        """Возвращает все RTSP-потоки из хранилища"""
        try:
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Ошибка чтения RTSP: {e}")
            return {}

    def remove_rtsp(self, name: str) -> bool:
        """Удаляет RTSP-поток из хранилища"""
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