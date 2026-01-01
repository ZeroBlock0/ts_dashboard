import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qfluentwidgets import Theme, setTheme

from app.common.config import load_config
from app.common.i18n import init_language
from app.ui.main_window import MainWindow

if __name__ == "__main__":
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)
    
    # Initialize Language
    init_language()
    
    # Load initial theme from config
    init_theme = Theme.LIGHT
    cfg = load_config()
    t = cfg.get("theme", "Light")
    
    if t == "Dark": 
        init_theme = Theme.DARK
    elif t == "System": 
        init_theme = Theme.AUTO
        
    setTheme(init_theme)
    
    w = MainWindow()
    w.show()
    
    sys.exit(app.exec())
