from PyQt6.QtCore import QObject
from rtsp.rtsp_manager import RtspManagerDialog
from rtsp.rtsp_storage import RtspStorage

class RtspManager(QObject):
    def __init__(self, main_controller):
        super().__init__()
        self.main = main_controller
        self.load_rtsp_list()
        
    def load_rtsp_list(self):
        try:
            rtsp_storage = RtspStorage()
            rtsp_list = rtsp_storage.get_all_rtsp()
            
            current_selection = self.main.ui.rtsp_combo.currentText()
            self.main.ui.rtsp_combo.clear()
            
            if rtsp_list:
                self.main.ui.rtsp_combo.addItems(sorted(rtsp_list.keys()))
                self.main.ui.rtsp_combo.setEnabled(True)
                
                if current_selection in rtsp_list:
                    self.main.ui.rtsp_combo.setCurrentText(current_selection)
            else:
                self.main.ui.rtsp_combo.addItem("Нет сохраненных RTSP")
                self.main.ui.rtsp_combo.setEnabled(False)
                
        except Exception as e:
            self.main.logger.error(f"Ошибка загрузки RTSP: {str(e)}")
            self.main.ui.rtsp_combo.clear()
            self.main.ui.rtsp_combo.addItem("Ошибка загрузки")

    def show_rtsp_dialog(self):
        try:      
            rtsp_storage = RtspStorage()
            dialog = RtspManagerDialog(rtsp_storage, self.main.ui)
            dialog.data_changed.connect(self.load_rtsp_list)
            dialog.exec()
        except Exception as e:
            self.main.logger.error(f"Ошибка открытия диалога RTSP: {str(e)}")
            self.main.ui.show_warning("Ошибка", "Не удалось открыть диалог управления RTSP")

    def get_current_rtsp(self):
        current_name = self.main.ui.rtsp_combo.currentText()
        if current_name:
            rtsp_storage = RtspStorage()
            return rtsp_storage.get_all_rtsp().get(current_name, {})
        return {}