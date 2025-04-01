from enum import Enum, auto
from typing import Optional, Tuple
import os
import re 

class InputType(Enum):
    CAMERA = auto()
    RTSP = auto()
    FILE = auto()
    IMAGE = auto()
    UNKNOWN = auto()

class InputValidator:
    CAMERA_REGEX = r'^\d+$'
    VIDEO_EXTENSIONS = ('.mp4', '.avi', '.mov', '.mkv')

    @classmethod
    def validate_input(cls, input_str: str, selected_source_type: int) -> Tuple[Optional[InputType], Optional[str], Optional[str]]:
        input_str = input_str.strip()
        if not input_str:
            return None, None, "Введите данные источника"

        source_types = {
            0: InputType.CAMERA,
            1: InputType.FILE,
            2: InputType.RTSP
        }
        expected_type = source_types.get(selected_source_type, InputType.UNKNOWN)

        if expected_type == InputType.CAMERA:
            if not re.fullmatch(cls.CAMERA_REGEX, input_str):
                return InputType.CAMERA, None, "Индекс камеры должен быть числом"
            return InputType.CAMERA, input_str, None

        if expected_type == InputType.FILE:
            if not os.path.exists(input_str):
                return InputType.FILE, None, "Видеофайл не найден"
            if not input_str.lower().endswith(cls.VIDEO_EXTENSIONS):
                return InputType.FILE, None, f"Поддерживаемые форматы: {', '.join(cls.VIDEO_EXTENSIONS)}"
            return InputType.FILE, input_str, None

        if expected_type == InputType.RTSP:
            from .rtsp_validator import RtspValidator
            is_valid, error_msg = RtspValidator.validate_rtsp_url(input_str)
            return (InputType.RTSP, input_str, None) if is_valid else (InputType.RTSP, None, error_msg)

        return InputType.UNKNOWN, None, "Неизвестный тип источника"