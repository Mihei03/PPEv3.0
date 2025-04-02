from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt, QSize

class ModelTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setup_table()
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._last_sorted_column = 0
        
    def setup_table(self):
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["№", "Название", "Комментарий"])
        
        header = self.horizontalHeader()
        header.setSectionsClickable(True)
        header.sectionClicked.connect(self._sort_table)
        header.setDefaultSectionSize(150)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        self.setColumnWidth(0, 50)   # №
        self.setColumnWidth(1, 200)  # Название
        # Комментарий - автоматически растягивается
        
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setWordWrap(True)
        self.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.verticalHeader().setDefaultSectionSize(40)
        self.verticalHeader().setVisible(False)
        
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
        
    def populate(self, models):
        self.setRowCount(len(models))
        for row, (model_name, info) in enumerate(models.items()):
            # Для сортировки по номеру используем числовое значение
            num_item = QTableWidgetItem()
            num_item.setData(Qt.ItemDataRole.DisplayRole, row + 1)
            
            name_item = QTableWidgetItem(model_name)
            comment_item = QTableWidgetItem(info.get('comment', ''))
            
            for item in [num_item, name_item, comment_item]:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.setItem(row, 0, num_item)
            self.setItem(row, 1, name_item)
            self.setItem(row, 2, comment_item)
            
            self.resizeRowToContents(row)
        
        # Сортируем после заполнения
        if self.rowCount() > 0:
            self.sortItems(self._last_sorted_column, self._sort_order)
    
    def get_selected(self):
        selected_items = self.selectedItems()
        if not selected_items:
            return None
            
        row = selected_items[0].row()
        return {
            'name': self.item(row, 1).text(),
            'comment': self.item(row, 2).text()
        }