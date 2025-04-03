from PyQt6.QtWidgets import QStatusBar, QPushButton, QSizePolicy

class StatusBar:
    def __init__(self, main_window):
        self.main_window = main_window
        self.bar = QStatusBar()
        self._setup_bar()
    
    def _setup_bar(self):
        self.bar.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Fixed
        )
        
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setObjectName("themeButton")
        self.theme_btn.setFixedSize(30, 30)
        self.bar.addPermanentWidget(self.theme_btn)
    
    def show_message(self, message, timeout=0):
        self.bar.showMessage(message, timeout)