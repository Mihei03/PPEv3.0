from PyQt6.QtCore import QObject
from models.model_manager import ModelManagerDialog

class ModelManager(QObject):
    def __init__(self, main_controller):
        super().__init__()
        self.main = main_controller
        self.current_model = None

    def activate_model(self):
        # Получаем доступ к комбобоксу через model_panel
        model_name = self.main.ui.model_panel.model_combo.currentText()
        if not model_name or model_name == "Нет доступных моделей":
            self.main.ui.status_bar.show_message("Не выбрана модель", 3000)
            return
            
        self.main.logger.info(f"Начало активации модели: {model_name}")
        self.main.ui_state_manager.set_ui_enabled(False)
        
        try:
            if self.main.model_handler.load_model(model_name):
                self.current_model = model_name
                self.main.ui.status_bar.show_message(f"Модель '{model_name}' активирована", 3000)
                self.main.ui.control_panel.start_btn.setEnabled(True)
            else:
                self.main.ui.status_bar.show_message("Ошибка активации модели", 3000)
        finally:
            self.main.ui_state_manager.set_ui_enabled(True)

    def on_model_loaded(self, model_name, model_info):
        if self.main.video_processor.load_model(model_name, model_info):
            self.current_model = model_name
            # Исправленный доступ к кнопке через control_panel
            self.main.ui.control_panel.start_btn.setEnabled(True)
            self.main.ui.status_bar.show_message(f"Модель '{model_name}' готова", 3000)
        else:
            self.main.ui.control_panel.start_btn.setEnabled(False)
            self.main.ui.status_bar.show_message(f"Ошибка инициализации модели '{model_name}'", 3000)

    def on_model_loading(self, model_name):
        self.main.ui.show_message(f"Загрузка модели {model_name}...")

    def refresh_models_list(self):
        models = self.main.model_handler.refresh_models_list()
        
        # Сохраняем текущий выбор
        current_model = self.main.ui.model_panel.model_combo.currentText()
        
        # Блокируем сигнал на время обновления
        self.main.ui.model_panel.model_combo.blockSignals(True)
        self.main.ui.model_panel.model_combo.clear()
        
        if models:
            self.main.ui.model_panel.model_combo.addItems(models)
            # Восстанавливаем предыдущий выбор, если он есть в новом списке
            if current_model in models:
                self.main.ui.model_panel.model_combo.setCurrentText(current_model)
            self.main.ui.status_bar.show_message(f"Доступно моделей: {len(models)}", 3000)
        else:
            self.main.ui.model_panel.model_combo.addItem("Нет доступных моделей")
        
        # Разблокируем сигнал
        self.main.ui.model_panel.model_combo.blockSignals(False)
        
        # Гарантированно блокируем кнопку только если модель не активирована
        if not self.main.model_handler.is_model_activated():
            self.main.ui.control_panel.start_btn.setEnabled(False)
    def show_models_dialog(self):
        try:
            dialog = ModelManagerDialog(self.main.model_handler, self.main.ui)
            dialog.models_updated.connect(self.refresh_models_list)
            dialog.exec()
        except Exception as e:
            self.main.logger.error(f"Ошибка открытия диалога моделей: {str(e)}")
            self.main.ui.show_warning("Ошибка", "Не удалось открыть диалог управления моделями")