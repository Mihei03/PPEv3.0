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
        start_time = time.time()  # Для замера времени
        
        input_type, normalized_source, error_msg = InputValidator.validate_input(
            source, selected_source_type
        )
        
        if error_msg:
            return False, error_msg

        # Освобождаем предыдущий источник
        if self.cap:
            self.cap.release()
        
        try:
            # Оптимизация для камеры
            if input_type == InputType.CAMERA:
                camera_index = int(normalized_source)
                self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)  # Используем DirectShow для Windows
                if self.cap.isOpened():
                    # Устанавливаем оптимальные параметры
                    self.cap.set(cv2.CAP_PROP_FPS, 30)          # Фиксируем FPS
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)    # Минимальный буфер
                    self.current_input_type = input_type
                    self.logger.info(f"Камера инициализирована за {(time.time()-start_time):.2f} сек")
                    return True, None
            
            # Оптимизация для RTSP
            elif input_type == InputType.RTSP:
                # Оптимальные параметры для RTSP
                rtsp_url = self._prepare_rtsp_url(normalized_source)
                self.cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                
                if self.cap.isOpened():
                    # Критически важные настройки для RTSP
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Минимальный буфер
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
                    self.cap.set(cv2.CAP_PROP_POS_MSEC, 0)
                    
                    # Отключаем перекодирование
                    self.cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
                    self.cap.set(cv2.CAP_PROP_HW_DEVICE, 0)  # Используем GPU если доступно
                    
                    self.logger.info(f"RTSP подключен с параметрами: {rtsp_url}")
                    return True, None
            
            # Для файлов
            elif input_type == InputType.FILE:
                self.cap = cv2.VideoCapture(normalized_source)
                if self.cap.isOpened():
                    self.current_input_type = input_type
                    self.logger.info(f"Видеофайл открыт за {(time.time()-start_time):.2f} сек")
                    return True, None
            
            return False, "Не удалось открыть источник"
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации источника: {str(e)}")
            return False, f"Ошибка: {str(e)}"

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
        """Явное освобождение ресурсов камеры"""
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
            self.logger.info("Ресурсы камеры освобождены")