from PyQt6.QtCore import QObject

class UIStateManager(QObject):
    def __init__(self, main_controller):
        super().__init__()
        self.main = main_controller

    def set_ui_enabled(self, enabled):
        widgets = [
            self.main.ui.model_panel.model_combo,
            self.main.ui.model_panel.activate_model_btn,
            self.main.ui.control_panel.start_btn
        ]
        for widget in widgets:
            widget.setEnabled(enabled)

    def update_start_button_style(self):
        self.main.ui.start_btn.style().unpolish(self.main.ui.start_btn)
        self.main.ui.start_btn.style().polish(self.main.ui.start_btn)
        self.main.ui.start_btn.update()