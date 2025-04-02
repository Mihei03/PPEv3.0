import sys
import os
import cv2
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QFile, QTextStream, QSettings
from config import Config
from utils.logger import AppLogger
from PyQt6.QtGui import QIcon

def check_camera():
    """Проверка доступности камеры"""
    logger = AppLogger.get_logger()
    cap = cv2.VideoCapture(Config.CAMERA_INDEX)
    if not cap.isOpened():
        logger.warning("Камера не доступна")
        return False
    cap.release()
    return True

def load_stylesheet():
    """Загрузка стилей из файла"""
    try:
        style_path = os.path.join(os.path.dirname(__file__), 'ui', 'styles', 'styles.css')
        
        with open(style_path, 'r') as f:
            stylesheet = f.read()
            
        return stylesheet
    except Exception as e:
        AppLogger.get_logger().error(f"Ошибка загрузки стилей: {str(e)}")
        return ""

def check_models():
    """Проверка доступности моделей с подробным логгированием"""
    logger = AppLogger.get_logger()
    try:
        from src.config import Config
        models = Config.get_available_models()
        
        if not models:
            logger.warning(f"Не найдены модели в папке: {Config.MODELS_ROOT}")
            return False
            
        logger.info(f"Найдены модели: {list(models.keys())}")
        
        # Проверка файлов для каждой модели
        for name, info in models.items():
            if not os.path.exists(info['pt_file']):
                logger.error(f"Файл модели не найден: {info['pt_file']}")
                return False
            if not os.path.exists(info['yaml_file']):
                logger.error(f"Конфиг модели не найден: {info['yaml_file']}")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Ошибка проверки моделей: {str(e)}", exc_info=True)
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
    app.setWindowIcon(QIcon('data/images/app_icon.png'))
    
    stylesheet = load_stylesheet()
    app.setStyleSheet(stylesheet)

    settings = QSettings("MyCompany", "SIZDetector")
    dark_mode = settings.value("dark_mode", False, type=bool)

    if dark_mode:
        app.setProperty("class", "dark-mode")
    else:
        app.setProperty("class", "")

    # Показать предупреждения (не блокирующие)
    show_warning_messages(app)
    
    try:
        from src.ui.ui_window import MainWindowUI
        from src.ui.main_controller import MainController
        window = MainWindowUI()
        controller = MainController(window)

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