from PyQt6.QtCore import QObject
from rtsp.rtsp_manager import RtspManagerDialog
from rtsp.rtsp_storage import RtspStorage

class RtspManager(QObject):
    def __init__(self, main_controller):
        super().__init__()
        self.main = main_controller
        self.rtsp_storage = RtspStorage()

    def load_rtsp_list(self):
        """Теперь этот метод должен вызываться явно после полной инициализации UI"""
        try:
            rtsp_storage = RtspStorage()
            rtsp_list = rtsp_storage.get_all_rtsp()
            
            # Получаем доступ к rtsp_combo через control_panel
            current_selection = self.main.ui.ui_builder.control_panel.rtsp_combo.currentText()
            self.main.ui.ui_builder.control_panel.rtsp_combo.clear()
            
            if rtsp_list:
                self.main.ui.ui_builder.control_panel.rtsp_combo.addItems(sorted(rtsp_list.keys()))
                self.main.ui.ui_builder.control_panel.rtsp_combo.setEnabled(True)
                
                if current_selection in rtsp_list:
                    self.main.ui.ui_builder.control_panel.rtsp_combo.setCurrentText(current_selection)
                # Добавляем сообщение об успешной загрузке
                self.main.ui.status_bar.show_message("RTSP потоки загружены", 3000)
            else:
                self.main.ui.ui_builder.control_panel.rtsp_combo.addItem("Нет сохраненных RTSP")
                self.main.ui.ui_builder.control_panel.rtsp_combo.setEnabled(False)
                self.main.ui.status_bar.show_message("Нет сохраненных RTSP потоков", 3000)
                
        except Exception as e:
            self.main.logger.error(f"Ошибка загрузки RTSP: {str(e)}")
            self.main.ui.ui_builder.control_panel.rtsp_combo.clear()
            self.main.ui.ui_builder.control_panel.rtsp_combo.addItem("Ошибка загрузки")
            # Добавляем сообщение об ошибке
            self.main.ui.status_bar.show_message("Ошибка загрузки RTSP потоков", 3000)

    def show_rtsp_dialog(self):
        try:      
            rtsp_storage = RtspStorage()
            dialog = RtspManagerDialog(rtsp_storage, self.main.ui)
            dialog.data_changed.connect(self.load_rtsp_list)
            dialog.exec()
            # Добавляем сообщение после закрытия диалога
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
        current_name = self.main.ui.ui_builder.control_panel.rtsp_combo.currentText()
        if current_name and current_name != "Нет сохраненных RTSP":
            rtsp_storage = RtspStorage()
            return rtsp_storage.get_all_rtsp().get(current_name, {})
        return {}