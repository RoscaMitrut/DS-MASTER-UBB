from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QProgressBar, QTabWidget, QMessageBox, QRadioButton, 
                             QButtonGroup, QInputDialog, QFileDialog, QFrame,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, 
                             QLineEdit, QScrollArea, QFormLayout, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize

class AdjustableTextEdit(QTextEdit):

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setPlainText(str(text))
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        self.setFixedHeight(60)
        # self.adjust_height()

    def adjust_height(self):
        doc_height = self.document().size().height()
        margins = self.contentsMargins()
        total_height = int(doc_height + margins.top() + margins.bottom() + 10)
        
        self.setMinimumHeight(60)
        self.setMaximumHeight(min(total_height, 120))
        self.setFixedHeight(min(total_height, 120))