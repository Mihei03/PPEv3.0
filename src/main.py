import sys
import os
import cv2
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QSettings
from config import Config
from core.utils.logger import AppLogger
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
    """Загрузка стилей из файла с проверкой пути"""
    logger = AppLogger.get_logger()
    try:
        # Получаем абсолютный путь к файлу стилей
        base_dir = os.path.dirname(os.path.abspath(__file__))
        style_path = os.path.join(base_dir, 'ui', 'styles', 'styles.css')
        
        # Проверяем существование файла
        if not os.path.exists(style_path):
            logger.error(f"Файл стилей не найден: {style_path}")
            return ""
            
        # Читаем файл с указанием кодировки
        with open(style_path, 'r', encoding='utf-8') as f:
            stylesheet = f.read()
            
        logger.info("Стили успешно загружены")
        return stylesheet
    except Exception as e:
        logger.error(f"Ошибка загрузки стилей: {str(e)}", exc_info=True)
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
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Предупреждение")
        msg_box.setText("Камера не доступна! Некоторые функции будут недоступны.")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        
        # Применяем текущую тему к QMessageBox
        if app.property("class") == "dark-mode":
            msg_box.setProperty("class", "dark-mode")
            msg_box.setStyleSheet(app.styleSheet())
            
        msg_box.exec()
    cap.release()

def main():
    logger = AppLogger.get_logger()
    logger.info("Запуск приложения")
    
    # Добавление корневой директории в PYTHONPATH
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(root_dir)
    
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('data/images/app_icon.png'))
    
    # Загрузка и применение стилей ДО создания главного окна
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
    else:
        logger.warning("Не удалось загрузить стили")

    # Настройка темы
    settings = QSettings("MyCompany", "SIZDetector")
    dark_mode = settings.value("dark_mode", False, type=bool)
    app.setProperty("class", "dark-mode" if dark_mode else "")

    # Показать предупреждения (не блокирующие)
    show_warning_messages(app)
    
    try:
        from src.core.controllers.main_controller import MainController
        from src.ui.ui_window import MainWindowUI
        
        # Создание окна ПОСЛЕ применения стилей
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
        logger.error(f"Не удалось запустить приложение: {str(e)}", exc_info=True)
        QMessageBox.critical(None, "Ошибка", f"Критическая ошибка: {str(e)}")
        sys.exit(1)
    
if __name__ == "__main__":
    main()