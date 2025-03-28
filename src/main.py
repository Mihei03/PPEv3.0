import sys
import os
import cv2
from PyQt6.QtWidgets import QApplication, QMessageBox
from config import Config
from utils.logger import AppLogger

def check_camera():
    """Проверка доступности камеры с записью в лог"""
    logger = AppLogger.get_logger()
    try:
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)
        if not cap.isOpened():
            logger.warning("Камера не доступна! Приложение запустится без видеоввода")
            return False
        cap.release()
        logger.info("Камера успешно подключена")
        return True
    except Exception as e:
        logger.error(f"Ошибка проверки камеры: {str(e)}")
        return False

def check_models():
    """Проверка наличия моделей с записью в лог"""
    logger = AppLogger.get_logger()
    try:
        models = Config.get_available_models()
        if not models:
            logger.warning(f"Не найдены модели в папке: {Config.MODELS_ROOT}")
            return False
        logger.info(f"Найдены модели: {list(models.keys())}")
        return True
    except Exception as e:
        logger.error(f"Ошибка проверки моделей: {str(e)}")
        return False

def show_warning_messages(app):
    """Показать предупреждения (но не блокировать запуск)"""
    # Проверка камеры
    cap = cv2.VideoCapture(Config.CAMERA_INDEX)
    if not cap.isOpened():
        QMessageBox.warning(None, "Предупреждение", 
            "Камера не доступна! Некоторые функции будут недоступны.")
    cap.release()

def main():
    logger = AppLogger.get_logger()
    logger.info("Запуск приложения")
    
    # Добавление корневой директории в PYTHONPATH
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(root_dir)
    
    app = QApplication(sys.argv)
    
    # Проверки (только для логирования)
    check_camera()
    check_models()
    
    # Показать предупреждения (не блокирующие)
    show_warning_messages(app)
    
    try:
        from src.ui.main_window import MainWindow
        window = MainWindow()
        
        # Проверяем необходимые атрибуты
        if not hasattr(window, 'video_processor'):
            raise AttributeError("Отсутствует video_processor")
            
        required_methods = ['load_model', 'start_processing', 'stop_processing']
        for method in required_methods:
            if not hasattr(window.video_processor, method):
                raise AttributeError(f"VideoProcessor отсутствует метод {method}")
        
        window.show()
        status_message = "Система инициализирована"
        if not check_camera():
            status_message += " (камера не доступна)"
        if not check_models():
            status_message += " (модели не найдены)"
        
        window.statusBar().showMessage(status_message, 3000)
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Не удалось запустить приложение: {str(e)}")
        QMessageBox.critical(None, "Ошибка", f"Критическая ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()