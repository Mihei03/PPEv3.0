from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
from src.utils.drawing_utils import draw_landmarks, draw_siz_status

class VideoProcessor(QObject):
    update_frame_signal = pyqtSignal(QImage)
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_frame)
        self.show_landmarks = True
        self.yolo_model = None
        
    def on_model_loaded(self, model_info):
        if model_info:
            self.parent.yolo_detector.load_model(model_info)
            self.yolo_model = model_info
        
    def toggle_landmarks(self, state):
        self.show_landmarks = state
        
    def start_processing(self):
        if not self.timer.isActive():
            self.timer.start(30)  # 30ms = ~33 FPS
            
    def stop_processing(self):
        self.timer.stop()
        
    def process_frame(self):
        if not self.parent.cap.isOpened():
            return
            
        ret, frame = self.parent.cap.read()
        if not ret:
            return
            
        # Обработка кадра
        pose_results = self.parent.pose_detector.detect(frame)
        face_results = self.parent.face_detector.detect(frame)
        
        # Детекция YOLO
        yolo_boxes = None
        if self.yolo_model and self.parent.yolo_detector.model:
            frame, yolo_boxes = self.parent.yolo_detector.detect(frame)
        
        # Отрисовка элементов
        if self.show_landmarks:
            draw_landmarks(frame, pose_results, face_results)
            
        # Всегда отображаем статус СИЗ
        siz_detected = False
        if yolo_boxes:
            siz_statuses = self.parent.siz_detector.detect_multiple(
                pose_results, face_results, yolo_boxes, frame.shape
            )
            siz_detected = all(siz_statuses) if siz_statuses else False
        draw_siz_status(frame, siz_detected)
        
        # Конвертация в QImage
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        self.update_frame_signal.emit(q_image)