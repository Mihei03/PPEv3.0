from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QFileDialog
import os

class ProcessingManager(QObject):
    def __init__(self, main_controller):
        super().__init__()
        self.main = main_controller
        self.current_siz_status = None

    def on_start_stop(self):
        if self.main.processing_active:
            self.on_stop_processing()
        else:
            self.on_start_processing()

    def on_start_processing(self):
        try:
            source_type = self.main.ui.control_panel.source_type.currentIndex()
            source = self.main.ui.control_panel.source_input.text().strip()
            # Проверяем активацию модели
            if not self.main.model_handler.is_model_activated():
                self._show_error_message(
                    "Модель не активирована",
                    "Перед запуском анализа необходимо активировать модель"
                )
                return

            source_type = self.main.ui.control_panel.source_type.currentIndex()
            source = self.main.ui.control_panel.source_input.text().strip()

            # Проверка для камеры
            if source_type == 0:
                try:
                    camera_idx = int(source)
                    if camera_idx < 0:
                        raise ValueError("Индекс камеры должен быть ≥ 0")
                except ValueError as e:
                    self._show_error_message("Неверный индекс камеры", str(e))
                    return

            # Проверка для файлового источника
            elif source_type == 1:
                if not source or source == "0":
                    self._show_error_message(
                        "Файл не выбран",
                        "Пожалуйста, выберите видеофайл для анализа"
                    )
                    return
                if not os.path.exists(source):
                    self._show_error_message(
                        "Файл не найден",
                        f"Указанный файл не существует:\n{source}"
                    )
                    return

            # Проверка для RTSP
            elif source_type == 2:
                rtsp_data = self.main.rtsp_manager.get_current_rtsp()
                if not rtsp_data or not rtsp_data.get("url"):
                    self._show_error_message(
                        "RTSP не выбран",
                        "Пожалуйста, выберите RTSP поток из списка"
                    )
                    return
                source = rtsp_data["url"]

                if not rtsp_data.get("model"):
                    self._show_error_message(
                        "Модель не назначена",
                        "Для выбранного RTSP потока не назначена модель"
                    )
                    return
            
            # Инициализация источника
            success, error_msg = self.main.input_handler.setup_source(source, source_type)
            if not success:
                self._show_error_message("Ошибка источника", error_msg)
                return

            # Запуск обработки
            if self.main.video_processor.set_video_source(source, source_type):
                self.main.processing_active = True
                self.set_processing_state(True)
                self.main.video_processor.start_processing()
                self.main.ui.status_bar.show_message("Обработка запущена", 3000)

        except Exception as e:
            self.main.processing_active = False
            self.set_processing_state(False)
            # Улучшенное сообщение об ошибке
            error_msg = str(e)
            if "input_handler" in error_msg:
                error_msg = "Ошибка инициализации видео источника"
            self._show_error_message(
                "Ошибка запуска",
                f"Не удалось запустить обработку:\n{error_msg}"
            )
            self.main.logger.error(f"Ошибка запуска обработки: {error_msg}")

    def _show_error_message(self, title, message):
        """Универсальный метод для показа сообщений об ошибках"""
        self.main.ui.show_warning(title, message)
        self.main.ui.status_bar.show_message(f"Ошибка: {message}", 5000)

    def on_stop_processing(self):
        self.main.processing_active = False
        self.main.video_processor.stop_processing()
        
        # Обновляем текст кнопки
        self.main.ui.control_panel.start_btn.setText("Запустить анализ")
        self.main.ui.control_panel.start_btn.setProperty("state", "")
        
        # Обновляем стиль кнопки
        self.main.ui.control_panel.start_btn.style().unpolish(self.main.ui.control_panel.start_btn)
        self.main.ui.control_panel.start_btn.style().polish(self.main.ui.control_panel.start_btn)
        self.main.ui.control_panel.start_btn.update()
        
        # Освобождаем ресурсы
        if hasattr(self.main, 'input_handler') and self.main.input_handler.cap:
            self.main.input_handler.release()
        
        status_message = f"Обработка остановлена | Модель: {self.main.model_manager.current_model}"
        self.main.ui.status_bar.show_message(status_message)

    def set_processing_state(self, active):
        """Обновленный метод с правильными путями доступа"""
        widgets = [
            self.main.ui.control_panel.source_type,
            self.main.ui.control_panel.source_input,
            self.main.ui.control_panel.browse_btn,
            self.main.ui.control_panel.rtsp_combo,
            self.main.ui.control_panel.add_rtsp_btn,
            self.main.ui.model_panel.model_combo,
            self.main.ui.model_panel.activate_model_btn,
            self.main.ui.model_panel.manage_models_btn
        ]
        
        for widget in widgets:
            widget.setEnabled(not active)
        
        if active:
            self.main.ui.control_panel.start_btn.setText("Остановить анализ")
            self.main.ui.control_panel.start_btn.setProperty("state", "stop")
        else:
            self.main.ui.control_panel.start_btn.setText("Запустить анализ")
            self.main.ui.control_panel.start_btn.setProperty("state", "")
        
        # Обновляем стиль кнопки
        self.main.ui.control_panel.start_btn.style().unpolish(self.main.ui.control_panel.start_btn)
        self.main.ui.control_panel.start_btn.style().polish(self.main.ui.control_panel.start_btn)
        self.main.ui.control_panel.start_btn.update()
            
        self.main.ui.control_panel.start_btn.setEnabled(True)

    def update_source_type(self, index):
        placeholders = [
            "Введите индекс камеры (0, 1, ...)",
            "Введите путь к видеофайлу или выберите его через 'Обзор'", 
            "Выберите RTSP поток"
        ]
        # Используем правильный путь до source_input
        self.main.ui.control_panel.source_input.setPlaceholderText(placeholders[index])
        
        is_file = index == 1
        is_rtsp = index == 2
        
        self.main.ui.control_panel.browse_btn.setVisible(is_file)
        self.main.ui.control_panel.rtsp_combo.setVisible(is_rtsp)
        self.main.ui.control_panel.add_rtsp_btn.setVisible(is_rtsp)
        self.main.ui.control_panel.source_input.setVisible(not is_rtsp)
        
        # Очищаем поле при переключении на файл или RTSP
        if index != 0:  # Если не камера
            self.main.ui.control_panel.source_input.clear()
        else:
            # Только для камеры устанавливаем значение по умолчанию "0"
            self.main.ui.control_panel.source_input.setText("0")
        
        # Принудительно запускаем валидацию
        self.main.ui.control_panel._validate_current_input(self.main.ui.control_panel.source_input.text())

    def handle_file_browse(self):
        if self.main.ui.control_panel.source_type.currentIndex() != 1:
            return

        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path, _ = QFileDialog.getOpenFileName(
            self.main.ui,
            "Выберите видеофайл",
            desktop,
            "Video Files (*.mp4 *.avi *.mov *.mkv)"
        )
        
        if file_path:
            self.main.ui.control_panel.source_input.setText(file_path)
            self.validate_video_source(file_path)

    def validate_video_source(self, file_path):
        is_valid = os.path.exists(file_path)
        self.set_input_validation_style(is_valid)
        
        if is_valid:
            success = self.main.video_processor.set_video_source(file_path, 1)
            if not success:
                self.main.ui.status_bar.show_message("Не удалось загрузить видеофайл", 3000)
        else:
            self.main.ui.status_bar.show_message("Файл не существует", 3000)

    def set_input_validation_style(self, is_valid):
        """Исправленный доступ к source_input"""
        self.main.ui.control_panel.source_input.setProperty("valid", str(is_valid).lower())
        self.main.ui.control_panel.source_input.style().unpolish(self.main.ui.control_panel.source_input)
        self.main.ui.control_panel.source_input.style().polish(self.main.ui.control_panel.source_input)
        self.main.ui.control_panel.source_input.update()

    def update_siz_status(self, status_data):
        try:
            if isinstance(status_data, tuple) and len(status_data) == 3:
                statuses, people_count, detected_siz = status_data
            else:
                statuses = status_data
                people_count = 0
                detected_siz = {}

            # Получаем список ожидаемых СИЗ из текущей модели
            model_siz = []
            if hasattr(self.main, 'model_handler') and hasattr(self.main.model_handler, 'current_model_info'):
                model_info = self.main.model_handler.current_model_info
                if model_info and 'class_names' in model_info:
                    model_siz = [name for name in model_info['class_names'] 
                                if any(siz_type in name.lower() 
                                    for siz_type in ['glasses', 'glove', 'helmet', 'pants', 'vest'])]

            # Всегда показываем список ожидаемых СИЗ, даже если ничего не обнаружено
            if not detected_siz:
                message = f"СИЗ: ничего не обнаружено ({', '.join(model_siz)})" if model_siz else "СИЗ: ничего не обнаружено"
            else:
                # Проверяем, все ли необходимые СИЗ надеты в нужном количестве
                required_per_person = 2 if 'glove' in str(detected_siz.keys()).lower() else 1
                all_detected = all(
                    count >= (people_count * required_per_person if 'glove' in siz_type.lower() else people_count)
                    for siz_type, count in detected_siz.items()
                    if people_count > 0
                )
                
                if all_detected and people_count > 0:
                    message = "СИЗ: все на местах"
                else:
                    # Формируем список недостающих СИЗ
                    missing_parts = []
                    for siz_type, count in detected_siz.items():
                        required = (people_count * 2) if 'glove' in siz_type.lower() else people_count
                        if count < required:
                            missing_count = required - count
                            missing_parts.append(f"{missing_count}× {siz_type}")
                    
                    # Проверяем, есть ли СИЗ, которые вообще не были обнаружены
                    not_detected = [siz for siz in model_siz 
                                if siz.lower() not in [d.lower() for d in detected_siz.keys()]]
                    
                    if missing_parts or not_detected:
                        if missing_parts and not_detected:
                            message = f"СИЗ: не хватает ({', '.join(missing_parts)}), не обнаружены: {', '.join(not_detected)}"
                        elif missing_parts:
                            message = f"СИЗ: не хватает ({', '.join(missing_parts)})"
                        else:
                            message = f"СИЗ: не обнаружены следующие элементы: {', '.join(not_detected)}"
                    else:
                        # Если есть обнаруженные СИЗ, но они не на нужных местах
                        if any(not s for s in statuses) if isinstance(statuses, list) else not statuses:
                            message = f"СИЗ: обнаружены, но не надеты правильно ({', '.join(detected_siz.keys())})"
                        else:
                            message = f"СИЗ: не весь комплект надет ({', '.join(detected_siz.keys())})"
            
            base_msg = f"Модель: {self.main.model_manager.current_model} | " if self.main.model_manager.current_model else ""
            self.main.ui.show_message(base_msg + message)
            self.current_siz_status = all(statuses) if isinstance(statuses, list) else statuses
            
        except Exception as e:
            self.main.logger.error(f"Status update error: {str(e)}")
            self.main.ui.show_message("Ошибка обновления статуса")

    def on_input_error(self, error_msg):
        self.main.ui.status_bar.show_message(error_msg, 5000)
        self.main.ui.control_panel.start_btn.setEnabled(False)
        self.main.ui.show_warning("Ошибка источника", error_msg)