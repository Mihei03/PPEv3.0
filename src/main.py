import sys
import os
import cv2
from PyQt6.QtWidgets import QApplication, QMessageBox

def check_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        QMessageBox.critical(None, "Ошибка", "Камера не доступна!")
        return False
    cap.release()
    return True

def main():
    # Настройка путей
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(root_dir)
    
    # Проверка камеры
    app = QApplication(sys.argv)
    if not check_camera():
        sys.exit(1)
    
    try:
        from src.ui.main_window import MainWindow
        window = MainWindow()
        window.show()
        
        # Проверка видимости окна
        if not window.isVisible():
            window.showNormal()
            window.activateWindow()
            window.raise_()
        
        sys.exit(app.exec())
    except Exception as e:
        QMessageBox.critical(None, "Ошибка", f"Не удалось запустить приложение:\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()