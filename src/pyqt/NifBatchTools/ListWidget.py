import os

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QListWidget, QAbstractItemView


class NifList(QListWidget):
    def __init__(self, parent):
        super(NifList, self).__init__(parent)

        self.setSelectionMode(QAbstractItemView.MultiSelection)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("QListWidget {padding: 10px;} QListWidget::item { margin: 10px; }")
        self.setSortingEnabled(True)
        self.itemDoubleClicked.connect(self._open_file_location)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self._del_item()

    def _del_item(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))

    @staticmethod
    def _open_file_location(item):
        os.startfile(item.text(), 'open')

