from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage
import cv2
from src.utils.drawing_utils import draw_landmarks
from utils.logger import AppLogger

class VideoProcessor(QObject):
    update_frame_signal = pyqtSignal(QImage)
    siz_status_changed = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer()
        self.logger = AppLogger.get_logger()
        self.timer.timeout.connect(self._process_frame)
        self._setup_initial_state()
        self._init_camera()
        
    def _setup_initial_state(self):
        """Инициализация состояния процессора"""
        self.show_landmarks = True
        self.active_model_type = None
        self.model_loaded = False
        self.siz_detected = None
        self.processing_active = False
        self.detectors_ready = False

    def _init_camera(self):
        """Инициализация камеры с несколькими попытками"""
        for i in range(3):  # Пробуем разные индексы камер
            self.cap = cv2.VideoCapture(i)
            if self.cap.isOpened():
                self.logger.info(f"Камера инициализирована с индексом {i}")
                # Установим оптимальные параметры
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                return
        self.logger.error("Не удалось инициализировать камеру")
        self.cap = None

    def set_detectors(self, yolo, face, pose, siz):
        """Установка детекторов"""
        self.yolo = yolo
        self.face = face
        self.pose = pose
        self.siz = siz
        self.detectors_ready = True

    @pyqtSlot(str, dict)
    def load_model(self, model_type, model_info):
        """Загрузка модели детекции"""
        if not self.detectors_ready:
            return False
            
        try:
            if self.yolo.load_model(model_type, model_info):
                self.active_model_type = model_type
                # Добавляем имена классов в yolo.class_names
                if 'class_names' in model_info:
                    self.yolo.class_names[model_type] = model_info['class_names']
                self.model_loaded = True
                self.logger.info(f"Модель {model_type} загружена успешно")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модели: {str(e)}")
            return False

    @pyqtSlot()
    def start_processing(self):
        """Запуск обработки видео"""
        if not self.active_model_type:
            self.logger.warning("Активная модель не выбрана")
            return
            
        if not self.cap or not self.cap.isOpened():
            self._init_camera()  # Повторная инициализация при проблемах
            if not self.cap or not self.cap.isOpened():
                self.logger.error("Камера недоступна")
                return
            
        if not self.timer.isActive():
            self.processing_active = True
            self.timer.start(33)  # ~30 FPS
            self.logger.info("Началась обработка видео")

    @pyqtSlot()
    def stop_processing(self):
        """Остановка обработки видео"""
        if self.timer.isActive():
            self.timer.stop()
            self.processing_active = False
            self.logger.info("Обработка видео остановлена")

    def _process_frame(self):
        """Обработка кадра с переподключением камеры"""
        try:
            # Если камера не инициализирована, пытаемся подключиться
            if not self.cap or not self.cap.isOpened():
                self._init_camera()
                if not self.cap or not self.cap.isOpened():
                    self.logger.warning("Камера недоступна, пропускаем кадр")
                    QTimer.singleShot(1000, self._process_frame)  # Повтор через 1 сек
                    return

            # Чтение кадра
            ret, frame = self.cap.read()
            if not ret:
                self.logger.warning("Ошибка захвата кадра, переподключаем камеру")
                self.cap.release()
                self.cap = None
                QTimer.singleShot(1000, self._process_frame)  # Повтор через 1 сек
                return

            # Обработка кадра
            processed_frame = self._process_detections(frame)
            self._emit_frame(processed_frame)

        except Exception as e:
            self.logger.error(f"Критическая ошибка обработки: {str(e)}")
            self.stop_processing()


    def _process_detections(self, frame):
        """Обработка и детекция объектов с полной защитой от None"""
        frame = frame.copy()
        
        try:
            # Детекция ключевых точек
            face_results = self.face.detect(frame) if (self.show_landmarks and hasattr(self.face, 'detect')) else None
            pose_results = self.pose.detect(frame) if (self.show_landmarks and hasattr(self.pose, 'detect')) else None

            # Детекция объектов YOLO с защитой от ошибок
            boxes = None
            if self.active_model_type and hasattr(self.yolo, 'detect'):
                try:
                    _, boxes = self.yolo.detect(frame, self.active_model_type)
                except Exception as e:
                    self.logger.error(f"YOLO detection error: {str(e)}")
                    boxes = None

            # Обработка результатов детекции
            if boxes is not None and hasattr(boxes, 'xyxy') and len(boxes.xyxy) > 0:
                class_names = self.yolo.class_names.get(self.active_model_type, [])
                
                # Проверка соответствия СИЗ с защитой от ошибок
                statuses = []
                try:
                    statuses = self.siz.check_items(boxes, pose_results, face_results, frame.shape, class_names)
                except Exception as e:
                    self.logger.error(f"Compliance check error: {str(e)}")
                    statuses = [False] * len(boxes.xyxy)
                
                # Отправка статуса
                self.siz_status_changed.emit(statuses if statuses else False)
                
                # Отрисовка детекций
                frame = self._draw_detections_with_labels(frame, boxes, statuses, class_names)
            else:
                self.siz_status_changed.emit("nothing")

            # Отрисовка ключевых точек
            if self.show_landmarks:
                try:
                    if pose_results or face_results:
                        draw_landmarks(frame, pose_results, face_results)
                except Exception as e:
                    self.logger.error(f"Landmark drawing error: {str(e)}")

        except Exception as e:
            self.logger.error(f"Frame processing error: {str(e)}")
            self.siz_status_changed.emit(False)
        
        return frame

    def _draw_detections_with_labels(self, frame, boxes, statuses, class_names):
        """Безопасная отрисовка детекций"""
        try:
            if boxes is None or not hasattr(boxes, 'xyxy') or not hasattr(boxes, 'cls') or not hasattr(boxes, 'conf'):
                return frame
                
            for i, box in enumerate(boxes.xyxy):
                try:
                    x1, y1, x2, y2 = map(int, box.cpu().numpy())
                    status = statuses[i] if i < len(statuses) else False
                    
                    # Получаем класс и точность с защитой от ошибок
                    cls_id = int(boxes.cls[i].cpu().numpy()) if i < len(boxes.cls) else 0
                    conf = float(boxes.conf[i].cpu().numpy()) if i < len(boxes.conf) else 0.0
                    class_name = str(class_names[cls_id]) if (class_names and cls_id < len(class_names)) else f"Class {cls_id}"
                    
                    color = (0, 255, 0) if status else (0, 0, 255)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    label = f"{class_name} {conf:.2f}"
                    cv2.putText(frame, label, (x1, max(y1-10, 20)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                except Exception as e:
                    self.logger.warning(f"Error drawing box {i}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Drawing error: {str(e)}")
        
        return frame

    def _draw_detections(self, frame, boxes, statuses):
        """Отрисовка bounding boxes с классами и точностью"""
        for box, status, cls_id in zip(boxes.xyxy, statuses, boxes.cls):
            x1, y1, x2, y2 = map(int, box.cpu().numpy())
            conf = float(boxes.conf[boxes.cls.tolist().index(cls_id)])  # Получаем точность для текущего класса
            color = (0, 255, 0) if status else (0, 0, 255)
            
            # Получаем имя класса
            class_names = self.yolo.class_names.get(self.active_model_type, [])
            class_id = int(cls_id.cpu().numpy())
            class_name = str(class_names[class_id]) if class_names and class_id < len(class_names) else f"Class {class_id}"
            
            # Рисуем bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Подпись с классом и точностью
            label = f"{class_name} {conf:.2f}"
            cv2.putText(frame, label, (x1, y1-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return frame

    def _emit_frame(self, frame):
        """Конвертация и отправка кадра в UI"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.update_frame_signal.emit(q_img)
        except Exception as e:
            self.logger.error(f"Ошибка преобразования кадра: {str(e)}")

    def cleanup(self):
        """Очистка ресурсов"""
        self.stop_processing()
        if hasattr(self, 'cap') and self.cap and self.cap.isOpened():
            self.cap.release()
        self.logger.info("Ресурсы очищены")

    @pyqtSlot(bool)
    def toggle_landmarks(self, state):
        """Переключение отображения ключевых точек"""
        self.show_landmarks = state