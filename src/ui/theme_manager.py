from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QApplication, QWidget

class ThemeManager(QObject):
    def __init__(self, main_controller):
        super().__init__()
        self.main = main_controller
        self._dark_mode = self.main.settings.value("dark_mode", False, type=bool)
        self.load_theme_settings()

    def toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self.main.settings.setValue("dark_mode", self._dark_mode)
        self.update_theme_button()
        self.apply_theme(self._dark_mode)
        self.main.theme_changed.emit(self._dark_mode)

    def apply_theme(self, dark_mode):
        try:
            if dark_mode:
                self.main.ui.setProperty("class", "dark-mode")
            else:
                self.main.ui.setProperty("class", "")
            self.update_styles()
        except Exception as e:
            self.main.logger.error(f"Ошибка применения темы: {str(e)}")

    def update_styles(self):
        for widget in [self.main.ui] + self.main.ui.findChildren(QWidget):
            try:
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
            except:
                continue

    def update_theme_button(self):
        self.main.ui.theme_btn.setText("☀️" if self._dark_mode else "🌙")

    def load_theme_settings(self):
        self.update_theme_button()
        self.apply_theme(self._dark_mode)
        self.main.theme_changed.emit(self._dark_mode)