import re
from enum import Enum, auto
from typing import Optional, Tuple
import cv2
import os

class InputType(Enum):
    CAMERA = auto()
    RTSP = auto()
    FILE = auto()
    IMAGE = auto()
    UNKNOWN = auto()

class InputValidator:
    RTSP_REGEX = r'^rtsp://(?:[^:@\s]+:[^@\s]+@)?[a-zA-Z0-9.-]+(?::\d+)?(?:/[^\s]*)?$'
    PATH_REGEX = r'^(?:[a-zA-Z]:)?[\\/](?:[^\\/:*?"<>|\r\n]+[\\/])*[^\\/:*?"<>|\r\n]*$'
    CAMERA_REGEX = r'^\d+$'
    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

    @classmethod
    def validate_input(cls, input_str: str, selected_source_type: int) -> Tuple[Optional[InputType], Optional[str], Optional[str]]:
        input_str = input_str.strip()
        if not input_str:
            return None, None, "Введите данные источника"

        # Для RTSP просто проверяем начало строки, если это выбор из списка
        if selected_source_type == 2:  # RTSP поток
            if input_str.lower().startswith('rtsp://'):
                return InputType.RTSP, input_str, None
            return InputType.RTSP, None, "Выбранный поток не содержит валидный RTSP URL"

        # Определяем ожидаемый тип из UI
        SOURCE_TYPES = {
            0: InputType.CAMERA,
            1: InputType.FILE,
            2: InputType.RTSP
        }
        expected_type = SOURCE_TYPES.get(selected_source_type, InputType.UNKNOWN)

        # Валидация камеры
        if expected_type == InputType.CAMERA:
            if not re.fullmatch(cls.CAMERA_REGEX, input_str):
                return InputType.CAMERA, None, "Индекс камеры должен быть числом"
            return InputType.CAMERA, input_str, None

        # Валидация видеофайла
        if expected_type == InputType.FILE:
            if not os.path.exists(input_str):
                return InputType.FILE, None, "Видеофайл не найден"
            if not input_str.lower().endswith(cls.VIDEO_EXTENSIONS):
                return InputType.FILE, None, f"Поддерживаемые форматы: {', '.join(cls.VIDEO_EXTENSIONS)}"
            return InputType.FILE, input_str, None

        return InputType.UNKNOWN, None, "Неизвестный тип источника"


    @classmethod
    def _validate_rtsp_components(cls, rtsp_url: str) -> bool:
        """Дополнительная проверка компонентов RTSP ссылки"""
        try:
            # Удаляем префикс rtsp://
            if rtsp_url.lower().startswith('rtsp://'):
                rest = rtsp_url[7:]
            else:
                return False
                
            # Проверяем наличие хоста (минимальное требование)
            if '@' in rest:  # Случай с аутентификацией
                auth, host_part = rest.split('@', 1)
                if ':' in auth:
                    user, password = auth.split(':', 1)
                    if not user or not password:
                        return False
            else:
                host_part = rest
                
            # Хост может быть IP или доменным именем
            if ':' in host_part:  # Есть порт
                host, port = host_part.split(':', 1)
                if not port.isdigit():
                    return False
            else:
                host = host_part
                
            if not host:
                return False
                
            return True
        except:
            return False

    @classmethod
    def is_valid_camera_index(cls, index: int) -> bool:
        cap = cv2.VideoCapture(index)
        is_opened = cap.isOpened()
        cap.release()
        return is_opened