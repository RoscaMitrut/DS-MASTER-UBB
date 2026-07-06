from PyQt6.QtCore import QThread, pyqtSignal

class Worker(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    def __init__(self, task_func):
        super().__init__()
        self.task_func = task_func
    def run(self):
        result = self.task_func(self.progress_signal.emit)
        self.finished_signal.emit(str(result))
