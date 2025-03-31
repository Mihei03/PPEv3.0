from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, QSize

class RtspTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setup_table()
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._last_sorted_column = 0
        
    def setup_table(self):
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["№", "Имя", "Ссылка", "Комментарий"])
        
        # Настройка заголовков
        header = self.horizontalHeader()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self._sort_table)
        header.setDefaultSectionSize(150)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        # Установка размеров столбцов
        self.setColumnWidth(0, 50)  # №
        self.setColumnWidth(1, 150)  # Имя
        self.setColumnWidth(2, 300)  # Ссылка
        self.setColumnWidth(3, 200)  # Комментарий
        
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Включаем перенос текста и выравнивание
        self.setWordWrap(True)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.verticalHeader().setDefaultSectionSize(40)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.verticalHeader().setVisible(False)
        
        # Минимальный размер таблицы
        self.setMinimumSize(700, 300)

    def _sort_table(self, column):
        if self._last_sorted_column == column:
            self._sort_order = (
                Qt.SortOrder.DescendingOrder 
                if self._sort_order == Qt.SortOrder.AscendingOrder 
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._sort_order = Qt.SortOrder.AscendingOrder
            
        self.sortItems(column, self._sort_order)
        self._last_sorted_column = column
        
    def populate(self, data):
        self.setRowCount(len(data))
        for row, (name, info) in enumerate(data.items()):
            num_item = QTableWidgetItem(str(row + 1))
            name_item = QTableWidgetItem(name)
            url_item = QTableWidgetItem(info.get("url", ""))
            comment_item = QTableWidgetItem(info.get("comment", ""))
            
            # Настройка отображения текста
            for item in [num_item, name_item, url_item, comment_item]:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.setItem(row, 0, num_item)
            self.setItem(row, 1, name_item)
            self.setItem(row, 2, url_item)
            self.setItem(row, 3, comment_item)
            
            self.resizeRowToContents(row)
        
        if self.rowCount() > 0:
            self.sortItems(self._last_sorted_column, self._sort_order)