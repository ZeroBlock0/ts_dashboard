from PySide6.QtCore import QObject, Signal

# --- Signal Bridge for Thread Safety ---
class WorkerSignals(QObject):
    connected = Signal()
    disconnected = Signal()
    new_event = Signal(dict)
    query_response = Signal(dict)
    new_log = Signal(str, str)
