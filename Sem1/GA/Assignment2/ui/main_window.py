from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtCore import Qt
from database.manager import DatabaseManager
from services.ingestion import DataIngestionService
from services.view import ViewService
from services.labeling import LabelingService
from ui.tabs import DataTab, DataViewTab, LabelingTab

class MainWindow(QMainWindow):
    def __init__(self, workspace_name):
        super().__init__()
        self.setWindowTitle(f"Universal Labeler - Workspace: {workspace_name}")
        self.resize(1100, 850)

        self.db_manager = DatabaseManager(workspace_name)
        self.ingest_service = DataIngestionService(self.db_manager)
        self.view_service = ViewService(self.db_manager)
        self.label_service = LabelingService(self.db_manager)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        self.tab_data = DataTab(self.ingest_service)
        self.tab_view = DataViewTab(self.view_service)
        self.tab_label = LabelingTab(self.label_service)

        self.tabs.addTab(self.tab_data, "1. Import")
        self.tabs.addTab(self.tab_view, "2. View Data")
        self.tabs.addTab(self.tab_label, "3. Label Data")
        
        self.tabs.currentChanged.connect(self.on_tab_change)

        self.apply_styling()

    def on_tab_change(self, index):
        if index == 1:
            self.tab_view.load_table()

    def apply_styling(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #202124;
            }}
            
            QWidget {{
                background-color: #202124;
                color: #E8EAED;
                font-family: 'Segoe UI', 'Roboto', Helvetica, Arial, sans-serif;
                font-size: 14px; 
            }}
            
            QTabWidget::pane {{
                border: 1px solid #3C4043;
                background-color: #202124;
                border-top: none;
            }}
            
            QTabBar::tab {{
                background-color: #2D2F33;
                color: #9AA0A6;
                padding: 12px 25px;
                border: none;
                border-bottom: 2px solid #3C4043;
                font-weight: 500;
            }}
            
            QTabBar::tab:selected {{
                background-color: #202124;
                color: #0d7377;
                border-bottom: 2px solid #0d7377;
                font-weight: bold;
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: #35363A;
                color: #E8EAED;
            }}
            
            QPushButton {{
                background-color: #2D2F33;
                color: #E8EAED;
                border: 1px solid #5F6368;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }}
            
            QPushButton:hover {{
                background-color: #3C4043;
                border: 1px solid #9AA0A6;
            }}
            
            QPushButton:pressed {{
                background-color: #0d7377;
                border: 1px solid #0d7377;
            }}
            
            QTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox {{
                background-color: #171717;
                color: #E8EAED;
                border: 1px solid #3C4043;
                border-radius: 4px;
                padding: 8px;
            }}
            
            QTextEdit:focus, QLineEdit:focus {{
                border: 1px solid #0d7377;
                background-color: #1a1a1a;
            }}
            
            QComboBox {{
                background-color: #2D2F33;
                border: 1px solid #5F6368;
                border-radius: 4px;
                padding: 6px 10px;
                min-width: 6em;
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #5F6368;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid none;
                border-right: 5px solid none;
                border-top: 7px solid #E8EAED;
                margin-right: 6px; 
                width: 0; 
                height: 0;
            }}

            QComboBox QAbstractItemView {{
                background-color: #2D2F33;
                color: #E8EAED;
                border: 1px solid #5F6368;
                selection-background-color: #0d7377;
                selection-color: #ffffff;
            }}

            QCheckBox {{
                spacing: 8px;
                color: #E8EAED;
            }}

            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid #9AA0A6;
                border-radius: 3px;
                background: none;
            }}

            QCheckBox::indicator:unchecked:hover {{
                border-color: #E8EAED;
            }}

            QRadioButton {{
                spacing: 8px;
                color: #E8EAED;
            }}

            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid #9AA0A6;
                border-radius: 10px;
                background: none;
            }}

            QRadioButton::indicator:checked {{
                background-color: #0d7377;
                border: 2px solid #0d7377;
            }}

            QTableWidget {{
                background-color: #202124;
                gridline-color: #3C4043;
                border: 1px solid #3C4043;
            }}
            
            QHeaderView::section {{
                background-color: #2D2F33;
                color: #E8EAED;
                padding: 6px;
                border: 1px solid #3C4043;
                font-weight: bold;
            }}
            
            QTableWidget::item:selected {{
                background-color: #0d7377;
                color: #ffffff;
            }}
            
            QScrollBar:vertical {{
                border: none;
                background: #202124;
                width: 10px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background: #5F6368;
                min-height: 20px;
                border-radius: 5px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
        """)