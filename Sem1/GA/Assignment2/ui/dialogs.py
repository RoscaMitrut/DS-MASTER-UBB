import os
from PyQt6.QtWidgets import QInputDialog

def get_workspace_dialog():
    ws_dir = "workspaces"
    if not os.path.exists(ws_dir):
        os.makedirs(ws_dir)
    
    existing = [f.replace(".db", "") for f in os.listdir(ws_dir) if f.endswith(".db")]
    
    d = QInputDialog()
    d.setWindowTitle("Workspace Launcher")
    d.setLabelText("Enter new workspace name OR select existing:")
    d.setComboBoxItems(existing)
    d.setComboBoxEditable(True)
    
    if d.exec(): 
        return d.textValue()
    return None