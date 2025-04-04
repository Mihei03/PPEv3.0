import os
import time
import cv2
from core.utils.logger import AppLogger
from core.utils.input_validator import InputValidator, InputType

class InputHandler:
    def __init__(self):
        self.logger = AppLogger.get_logger()
        self.cap = None
        self.current_input_type = None
        self.camera_initialized = False

    def setup_source(self, source, selected_source_type):
        """Оптимизированная инициализация видео источника"""
        start_time = time.time()
        
        # Проверяем, что для файлового источника путь не пустой
        if selected_source_type == InputType.FILE and (not source or not source.strip()):
            return False, "Путь к видеофайлу не может быть пустым"
        
        input_type, normalized_source, error_msg = InputValidator.validate_input(
            source, selected_source_type
        )
        
        if error_msg:
            return False, error_msg

        if self.cap:
            self.cap.release()
        
        try:
            if input_type == InputType.CAMERA:
                camera_index = int(normalized_source)
                self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                
                # Добавляем проверку доступности камеры
                if not self.cap.isOpened():
                    error_msg = f"Камера с индексом {camera_index} недоступна"
                    self.logger.error(error_msg)
                    return False, error_msg
                    
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                self.current_input_type = input_type
                self.logger.info(f"Камера инициализирована за {(time.time()-start_time):.2f} сек")
                return True, None
            
            elif input_type == InputType.RTSP:
                rtsp_url = self._prepare_rtsp_url(normalized_source)
                self.cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    
                    if hasattr(cv2, 'CAP_PROP_HW_ACCELERATION'):
                        self.cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
                    
                    self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 500)
                    self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 500)
                    
                    self.logger.info(f"RTSP подключен: {rtsp_url}")
                    return True, None
            
            elif input_type == InputType.FILE:
                # Дополнительная проверка для файла
                if not normalized_source or not os.path.exists(normalized_source):
                    return False, "Файл не существует"
                    
                self.cap = cv2.VideoCapture(normalized_source)
                if self.cap.isOpened():
                    self.current_input_type = input_type
                    self.logger.info(f"Видеофайл открыт за {(time.time()-start_time):.2f} сек")
                    return True, None
            
            return False, "Не удалось открыть источник"
            
        except Exception as e:
            error_msg = f"Ошибка инициализации источника: {str(e)}"
            self.logger.error(error_msg)
            if self.cap:
                self.cap.release()
                self.cap = None
            return False, error_msg


    def get_frame(self):
        if not self.is_ready():
            self.logger.warning("Источник не готов")
            return None
            
        ret, frame = self.cap.read()
        return frame if ret else None

    def _prepare_rtsp_url(self, url):
        """Добавляем параметры для уменьшения задержки"""
        if '?' in url:
            return f"{url}&tcp_nodelay=1&buffer_size=1&rtsp_transport=tcp"
        return f"{url}?tcp_nodelay=1&buffer_size=1&rtsp_transport=tcp"

    def is_ready(self):
        return self.cap and self.cap.isOpened()

    def is_file_source(self):
        return self.current_input_type == InputType.FILE

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
            self.logger.info("Ресурсы камеры освобождены")
    
    def read_frame(self):
        """Чтение кадра с проверкой доступности"""
        if not self.is_ready():
            return None, None
            
        ret, frame = self.cap.read()
        if not ret:
            if self.is_file_source():
                self.logger.info("Достигнут конец видеофайла")
            return None, None
            
        return ret, frame