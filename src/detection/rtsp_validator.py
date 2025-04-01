import re
from typing import Optional, Tuple

class RtspValidator:
    RTSP_REGEX = r'^rtsp://(?:[^:@\s]+:[^@\s]+@)?[a-zA-Z0-9.-]+(?::\d+)?(?:/[^\s]*)?$'

    @classmethod
    def validate_rtsp_url(cls, rtsp_url: str) -> Tuple[bool, Optional[str]]:
        """Проверяет, является ли строка валидным RTSP-URL.
        
        Args:
            rtsp_url: Строка для проверки.
            
        Returns:
            Tuple[bool, Optional[str]]: 
                - True, если URL валиден, иначе False.
                - Сообщение об ошибке (если URL невалиден).
        """
        rtsp_url = rtsp_url.strip()
        if not rtsp_url:
            return False, "RTSP URL не может быть пустым"
        
        if not re.match(cls.RTSP_REGEX, rtsp_url, re.IGNORECASE):
            return False, (
                "Неверный формат RTSP ссылки. Примеры:\n"
                "rtsp://user:pass@host:port/path\n"
                "rtsp://host/path"
            )
        
        return True, None

    @classmethod
    def validate_rtsp_components(cls, rtsp_url: str) -> bool:
        """Дополнительная проверка компонентов RTSP (аутентификация, хост, порт)."""
        try:
            if not rtsp_url.lower().startswith('rtsp://'):
                return False

            rest = rtsp_url[7:]
            if '@' in rest:  # Аутентификация
                auth, host_part = rest.split('@', 1)
                if ':' in auth:
                    user, password = auth.split(':', 1)
                    if not user or not password:
                        return False
            else:
                host_part = rest

            if ':' in host_part:  # Порт
                host, port = host_part.split(':', 1)
                if not port.isdigit():
                    return False
            else:
                host = host_part

            return bool(host)
        except:
            return False