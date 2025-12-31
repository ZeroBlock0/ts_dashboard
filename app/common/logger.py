import logging

class QtLogHandler(logging.Handler):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals

    def emit(self, record):
        msg = self.format(record)
        self.signals.new_log.emit(record.levelname, msg)
