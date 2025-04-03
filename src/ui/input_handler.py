import cv2
from utils.logger import AppLogger
from src.detection.input_validator import InputValidator, InputType

class InputHandler:
    def __init__(self):
        self.logger = AppLogger.get_logger()
        self.cap = None
        self.current_input_type = None

    def setup_source(self, source, selected_source_type):
        input_type, normalized_source, error_msg = InputValidator.validate_input(
            source, selected_source_type
        )
        
        if error_msg:
            return False, error_msg

        if self.cap:
            self.cap.release()
        
        try:
            if input_type == InputType.CAMERA:
                self.cap = cv2.VideoCapture(int(normalized_source))
            elif input_type == InputType.RTSP:
                self.cap = cv2.VideoCapture(normalized_source, cv2.CAP_FFMPEG)
            elif input_type == InputType.FILE:
                self.cap = cv2.VideoCapture(normalized_source)
            
            if self.cap and self.cap.isOpened():
                self.current_input_type = input_type
                return True, None
            return False, "Не удалось открыть источник"
            
        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def get_frame(self):
        if not self.is_ready():
            self.logger.warning("Источник не готов")
            return None
            
        ret, frame = self.cap.read()
        return frame if ret else None

    def is_ready(self):
        return self.cap and self.cap.isOpened()

    def is_file_source(self):
        return self.current_input_type == InputType.FILE

    def release(self):
        if self.cap:
            self.cap.release()