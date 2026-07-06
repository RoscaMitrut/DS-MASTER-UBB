import sys
from PyQt6.QtWidgets import QApplication
from ui.dialogs import get_workspace_dialog
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    workspace_name = get_workspace_dialog()

    if workspace_name:
        window = MainWindow(workspace_name)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()