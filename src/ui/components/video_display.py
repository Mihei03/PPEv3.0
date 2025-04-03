from PyQt6.QtWidgets import (QScrollArea, QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                            QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

class VideoDisplay:
    def __init__(self, main_window):
        self.main_window = main_window
        self._setup_display()
        
    def _setup_display(self):
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.video_container = QWidget()
        self.video_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        self.video_layout = QHBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        
        self.center_container = QWidget()
        self.center_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        self.center_layout = QVBoxLayout(self.center_container)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.addStretch(1)
        
        self.video_label = QLabel()
        self.video_label.setObjectName("videoDisplay")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        
        self.center_layout.addWidget(self.video_label)
        self.center_layout.addStretch(1)
        
        self.video_layout.addStretch(1)
        self.video_layout.addWidget(self.center_container)
        self.video_layout.addStretch(1)
        
        self.scroll_area.setWidget(self.video_container)
    
    def update_frame(self, q_image):
        if not q_image.isNull():
            container_size = self.scroll_area.viewport().size()
            aspect_ratio = q_image.width() / q_image.height()
            
            max_width = container_size.width()
            max_height = int(max_width / aspect_ratio)
            
            if max_height > container_size.height():
                max_height = container_size.height()
                max_width = int(max_height * aspect_ratio)
            
            scaled_pixmap = QPixmap.fromImage(q_image).scaled(
                max_width, max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
            self.video_label.setFixedSize(scaled_pixmap.size())
            self.video_container.setMinimumSize(container_size)