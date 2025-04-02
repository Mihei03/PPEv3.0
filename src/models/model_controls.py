from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMessageBox

class ModelControls(QWidget):
    def __init__(self, manager_dialog):
        super().__init__()
        self.manager = manager_dialog
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить")
        self.edit_btn = QPushButton("Изменить")
        self.remove_btn = QPushButton("Удалить")
        
        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.remove_btn.clicked.connect(self._on_remove)
        
        layout.addWidget(self.add_btn)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.remove_btn)
        self.setLayout(layout)
    
    def _on_add(self):
        self.manager.add_model()
    
    def _on_edit(self):
        self.manager.edit_model()
    
    def _on_remove(self):
        self.manager.remove_model()