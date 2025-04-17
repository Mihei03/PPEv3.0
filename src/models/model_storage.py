from pathlib import Path
import sqlite3
from typing import Dict
from config import Config
from core.utils.logger import AppLogger
from sql_scripts import SQL


class ModelStorage:
  def __init__(self, storage_path: str = None):
        self.logger = AppLogger.get_logger()
        default_path = "data/config/" + Config.DB_NAME
        self.storage_file = Path(storage_path) if storage_path else Path(default_path)
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_storage_exists()

  def _ensure_storage_exists(self):
      """Создаёт файл хранилища, если он не существует"""

      with sqlite3.connect(self.storage_file) as con:
          con.executescript(SQL.INIT_DB)
          self.logger.info(f"Создан новый файл хранилища: {self.storage_file}")

  def add_model(self, filepath: str, comment: str = ""):
      try:
          #NOTE: тут надо путь провалидировать
          with sqlite3.connect(self.storage_file) as con:
              c = con.cursor()
              c.execute("INSERT INTO camera_models (file_path, comment) VALUES (?,?)", (filepath, comment))
              return True
      except Exception as e:
            self.logger.error(f"Ошибка добавления модели: {e}")
            return False
          
  def get_all_models(self) -> Dict[int]:
      try:
          with sqlite3.connect(self.storage_file) as con:
              c = con.cursor()
              c.execute("SELECT id, file_name, comment FROM cameras")
              items = c.fetchall()
                              
              res = {
                  id: {"file_name": filename, "comment": comment} for id, filename, comment in items
              }
              
              return res

      except Exception as e:
          self.logger.error(f"Ошибка чтения модели: {e}")
          return {}
      
    
  def remove_model(self, id: int) -> bool:
        try:
            with sqlite3.connect(self.storage_file) as con:
                c = con.cursor()
                c.execute("DELETE FROM camera_models WHERE id=?", (id,))
                
            return True

        except Exception as e:
            self.logger.error(f"Ошибка удаления модели: {e}")
            return False