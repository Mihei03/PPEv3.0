from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QMessageBox
from rtsp.rtsp_manager import RtspManagerDialog
from rtsp.rtsp_storage import RtspStorage

class RtspManager(QObject):
    def __init__(self, main_controller):
        super().__init__()
        self.main = main_controller
        self.rtsp_storage = RtspStorage()

    def load_rtsp_list(self):
        """Обновляет список RTSP потоков в выпадающем списке"""
        try:
            rtsp_list = self.rtsp_storage.get_all_rtsp()
            combo = self.main.ui.control_panel.rtsp_combo
            current_text = combo.currentText()
            
            combo.blockSignals(True)  # Блокируем сигналы во время обновления
            combo.clear()
            
            if rtsp_list:
                combo.addItems(sorted(rtsp_list.keys()))
                combo.setEnabled(True)
                
                # Пытаемся восстановить предыдущий выбор, если он еще существует
                if current_text in rtsp_list:
                    combo.setCurrentText(current_text)
                else:
                    combo.setCurrentIndex(0)
                
                # Сразу проверяем валидность выбора после обновления
                self.validate_rtsp_selection()
            else:
                combo.addItem("Нет сохраненных RTSP")
                combo.setEnabled(False)
                self.validate_rtsp_selection()
            
            combo.blockSignals(False)  # Разблокируем сигналы
            
        except Exception as e:
            self.main.logger.error(f"Ошибка загрузки RTSP: {str(e)}")
            self.main.ui.control_panel.rtsp_combo.clear()
            self.main.ui.control_panel.rtsp_combo.addItem("Ошибка загрузки")
            self.validate_rtsp_selection()

    def show_rtsp_dialog(self):
        try:      
            dialog = RtspManagerDialog(self.rtsp_storage, self.main.model_handler, self.main.ui)
            dialog.data_changed.connect(self.load_rtsp_list)
            dialog.exec()
            self.main.ui.status_bar.show_message("Диалог управления RTSP закрыт", 2000)
        except Exception as e:
            self.main.logger.error(f"Ошибка открытия диалога RTSP: {str(e)}")
            self.main.ui.status_bar.show_message("Ошибка открытия диалога RTSP", 3000)
            self.main.ui.show_warning("Ошибка", "Не удалось открыть диалог управления RTSP")

    def check_rtsp_model(self, rtsp_name):
        rtsp_data = self.get_current_rtsp()
        if rtsp_data and 'model' in rtsp_data and rtsp_data['model']:
            return True
        return False

    def get_current_rtsp(self):
        current_name = self.main.ui.control_panel.rtsp_combo.currentText()
        if current_name and current_name != "Нет сохраненных RTSP":
            return self.rtsp_storage.get_all_rtsp().get(current_name, {})
        return {}
    
    def validate_rtsp_selection(self):
        """Проверяет выбранный RTSP поток и обновляет UI"""
        if self.main.ui.control_panel.source_type.currentIndex() != 2:
            return False  # Не RTSP источник
        
        current_name = self.main.ui.control_panel.rtsp_combo.currentText()
        if not current_name or current_name == "Нет сохраненных RTSP":
            self._update_start_button(False, "Выберите RTSP поток из списка")
            return False
            
        rtsp_data = self.get_current_rtsp()
        if not rtsp_data:
            self._update_start_button(False, "Ошибка загрузки данных RTSP")
            return False
            
        if not rtsp_data.get('model'):
            self._update_start_button(False, f"Для '{current_name}' не назначена модель")
            QMessageBox.warning(
                self.main.ui,
                "Ошибка",
                f"Для RTSP потока '{current_name}' не назначена модель"
            )
            return False
            
        self._update_start_button(True, "RTSP поток готов к анализу")
        return True

    def _update_start_button(self, enabled, message=None):
        """Обновляет состояние кнопки запуска"""
        btn = self.main.ui.control_panel.start_btn
        btn.setEnabled(enabled)
        btn.setProperty("state", "valid" if enabled else "")
        
        # Обновляем стиль
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.update()
        
        if message:
            self.main.ui.status_bar.show_message(message, 3000)