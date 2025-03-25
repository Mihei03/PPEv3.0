import sys
import os
import cv2
from PyQt6.QtWidgets import QApplication, QMessageBox
from config import Config
from utils.logger import AppLogger

def check_camera():
    cap = cv2.VideoCapture(Config.CAMERA_INDEX)
    if not cap.isOpened():
        QMessageBox.critical(None, "Ошибка", "Камера не доступна!")
        return False
    cap.release()
    return True

def check_models():
    models = Config.get_available_models()
    if not models:
        QMessageBox.critical(None, "Ошибка", 
            f"Не найдены модели в папке:\n{Config.MODELS_ROOT}\n"
            f"Поместите модели в формате: /models/your_model/[model.pt, data.yaml]")
        return False
    return True

def main():
    logger = AppLogger.get_logger()
    logger.info("Запуск приложения")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(root_dir)
    
    app = QApplication(sys.argv)
    if not check_camera() or not check_models():
        sys.exit(1)
    
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
        window.statusBar().showMessage("Система инициализирована", 3000)
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Не удалось запустить приложение: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()