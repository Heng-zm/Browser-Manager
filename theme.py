# theme.py

LIGHT_STYLESHEET = """
    /* General Window & Widgets */
     QTextEdit#LogBox {
        background-color: #fdfdfd; 
        color: #008040; 
        font-family: 'Consolas', monospace; 
        border-radius: 4px; 
        border: 1px solid #dcdcdc;
    }
    QFormLayout::label {
        font-weight: 500;
        padding-top: 2px;
    }
    QMainWindow, QWidget { 
        background-color: #f0f0f0; 
        color: #111; 
        font-family: 'Segoe UI', sans-serif; 
        font-size: 14px; 
    }
    QTabWidget::pane { 
        border: 1px solid #dcdcdc;
        background-color: #ffffff;
        border-radius: 8px; 
    }
    QTabBar::tab { 
        background: #e1e1e1; 
        color: #555; 
        padding: 12px 25px; 
        border-top-left-radius: 6px; 
        border-top-right-radius: 6px; 
        margin-right: 2px; 
        font-weight: bold; 
        border: 1px solid #dcdcdc;
        border-bottom: none;
    }
    QTabBar::tab:selected { 
        background: #ffffff; 
        color: #0078d7; 
        border-bottom: 2px solid #0078d7; 
    }
    QLabel#SectionTitle {
        font-size: 16px;
        font-weight: bold;
        color: #005a9e;
        margin-top: 15px;
        margin-bottom: 5px;
    }
    QLineEdit, QSpinBox, QComboBox, QPlainTextEdit { 
        background-color: #ffffff; 
        border: 1px solid #c0c0c0; 
        border-radius: 4px; 
        padding: 8px; 
        color: #111; 
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {
        border-color: #0078d7;
    }
    QPushButton { 
        background-color: #e1e1e1; 
        color: #111; 
        border: 1px solid #c0c0c0;
        padding: 10px 20px; 
        border-radius: 5px; 
        font-weight: 600; 
    }
    QPushButton:hover { background-color: #ececec; }
    QPushButton:disabled { background-color: #f5f5f5; color: #aaa; border-color: #ddd; }
    QPushButton#PrimaryBtn { 
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078d7, stop:1 #005a9e); 
        color: white;
        font-size: 16px; 
        border: none;
    }
    QPushButton#PrimaryBtn:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0084e8, stop:1 #006ab3); }
    QPushButton#DangerBtn { background-color: #d32f2f; color: white; border: none; }
    QPushButton#DangerBtn:hover { background-color: #e54c4c; }
    QProgressBar { 
        border: 1px solid #c0c0c0; 
        border-radius: 4px; 
        text-align: center; 
        background-color: #e8e8e8; 
        color: #111;
        font-weight: bold;
    }
    QProgressBar::chunk { background-color: #00b862; border-radius: 3px; }
    QFrame#Divider { background-color: #dcdcdc; }
    QTextEdit#LogBox {
        background-color: #fdfdfd; 
        color: #008040; 
        font-family: 'Consolas', monospace; 
        border-radius: 4px; 
        border: 1px solid #dcdcdc;
    }
"""

DARK_STYLESHEET = """
    /* General Window & Widgets */
     QTextEdit#LogBox {
        background-color: #111; 
        color: #00cc66; 
        font-family: 'Consolas', monospace; 
        border-radius: 4px; 
        border: 1px solid #333;
    }
    QFormLayout::label {
        font-weight: 500;
        padding-top: 2px;
    }
    QMainWindow, QWidget { 
        background-color: #1e1e1e; 
        color: #e0e0e0; 
        font-family: 'Segoe UI', sans-serif; 
        font-size: 14px; 
    }
    QTabWidget::pane { 
        border: 1px solid #333;
        background-color: #252526;
        border-radius: 8px; 
    }
    QTabBar::tab { 
        background: #2d2d2d; 
        color: #aaa; 
        padding: 12px 25px; 
        border-top-left-radius: 6px; 
        border-top-right-radius: 6px; 
        margin-right: 2px; 
        font-weight: bold; 
    }
    QTabBar::tab:selected { 
        background: #252526; 
        color: #56c5ff; 
        border-bottom: 2px solid #56c5ff; 
    }
    QLabel#SectionTitle {
        font-size: 16px;
        font-weight: bold;
        color: #56c5ff;
        margin-top: 15px;
        margin-bottom: 5px;
    }
    QLineEdit, QSpinBox, QComboBox, QPlainTextEdit { 
        background-color: #333; 
        border: 1px solid #444; 
        border-radius: 4px; 
        padding: 8px; 
        color: #f0f0f0; 
    }
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {
        border-color: #56c5ff;
    }
    QPushButton { 
        background-color: #3e3e3e; 
        color: white; 
        border: 1px solid #555;
        padding: 10px 20px; 
        border-radius: 5px; 
        font-weight: 600; 
    }
    QPushButton:hover { background-color: #4f4f4f; }
    QPushButton:disabled { background-color: #2a2a2a; color: #555; border-color: #444; }
    QPushButton#PrimaryBtn { 
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0078d7, stop:1 #005a9e); 
        color: white;
        font-size: 16px; 
        border: none;
    }
    QPushButton#PrimaryBtn:hover { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0084e8, stop:1 #006ab3); }
    QPushButton#DangerBtn { background-color: #c02f2f; color: white; border: none; }
    QPushButton#DangerBtn:hover { background-color: #d34f4f; }
    QProgressBar { 
        border: 1px solid #444; 
        border-radius: 4px; 
        text-align: center; 
        background-color: #333; 
        color: white;
        font-weight: bold;
    }
    QProgressBar::chunk { background-color: #00b862; border-radius: 3px; }
    QFrame#Divider { background-color: #333; }
    QTextEdit#LogBox {
        background-color: #111; 
        color: #00cc66; 
        font-family: 'Consolas', monospace; 
        border-radius: 4px; 
        border: 1px solid #333;
    }
"""
