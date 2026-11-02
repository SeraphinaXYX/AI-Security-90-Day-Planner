"""Dark theme stylesheet and color constants."""

# Color palette
BG_PRIMARY = "#1a1a2e"
BG_SECONDARY = "#16213e"
BG_TERTIARY = "#0f3460"
BG_CARD = "#1e2a4a"
BG_INPUT = "#0d1b36"

ACCENT_BLUE = "#4a9eff"
ACCENT_PURPLE = "#7c3aed"
ACCENT_CYAN = "#06b6d4"

TEXT_PRIMARY = "#e2e8f0"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"

STATUS_COMPLETED = "#22c55e"
STATUS_PENDING = "#94a3b8"
STATUS_OVERDUE = "#ef4444"
STATUS_SKIPPED = "#f97316"
STATUS_POSTPONED = "#eab308"
STATUS_TODAY = "#4a9eff"

BORDER_COLOR = "#2d3a5c"
HOVER_BG = "#253356"
SELECTED_BG = "#1e3a6e"

DARK_STYLESHEET = f"""
QMainWindow {{
    background-color: {BG_PRIMARY};
}}

QWidget {{
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
}}

QLabel[class="heading"] {{
    font-size: 22px;
    font-weight: bold;
    color: {ACCENT_BLUE};
}}

QLabel[class="subheading"] {{
    font-size: 16px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

QLabel[class="muted"] {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}

QLabel[class="stat-value"] {{
    font-size: 28px;
    font-weight: bold;
    color: {ACCENT_BLUE};
}}

QLabel[class="phase-label"] {{
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    color: {ACCENT_CYAN};
    letter-spacing: 1px;
}}

QPushButton {{
    background-color: {BG_TERTIARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {HOVER_BG};
    border-color: {ACCENT_BLUE};
}}

QPushButton:pressed {{
    background-color: {SELECTED_BG};
}}

QPushButton[class="primary"] {{
    background-color: {ACCENT_BLUE};
    color: white;
    border: none;
    font-weight: 600;
}}

QPushButton[class="primary"]:hover {{
    background-color: #3b8bef;
}}

QPushButton[class="success"] {{
    background-color: {STATUS_COMPLETED};
    color: white;
    border: none;
}}

QPushButton[class="success"]:hover {{
    background-color: #16a34a;
}}

QPushButton[class="warning"] {{
    background-color: {STATUS_POSTPONED};
    color: #1a1a2e;
    border: none;
}}

QPushButton[class="danger"] {{
    background-color: {STATUS_OVERDUE};
    color: white;
    border: none;
}}

QPushButton[class="nav"] {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 12px 20px;
    text-align: left;
    font-size: 14px;
    color: {TEXT_SECONDARY};
}}

QPushButton[class="nav"]:hover {{
    background-color: {HOVER_BG};
    color: {TEXT_PRIMARY};
}}

QPushButton[class="nav"]:checked {{
    background-color: {SELECTED_BG};
    color: {ACCENT_BLUE};
    font-weight: 600;
}}

QTextEdit, QPlainTextEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px;
    font-size: 13px;
}}

QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {ACCENT_BLUE};
}}

QLineEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}}

QLineEdit:focus {{
    border-color: {ACCENT_BLUE};
}}

QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: {SELECTED_BG};
}}

QSpinBox, QTimeEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 6px 12px;
}}

QProgressBar {{
    background-color: {BG_INPUT};
    border: none;
    border-radius: 8px;
    height: 16px;
    text-align: center;
    color: white;
    font-size: 11px;
    font-weight: bold;
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_BLUE}, stop:1 {ACCENT_PURPLE});
    border-radius: 8px;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    background: {BG_PRIMARY};
    width: 8px;
    margin: 0;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER_COLOR};
    min-height: 30px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {TEXT_MUTED};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {BG_PRIMARY};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: {BORDER_COLOR};
    min-width: 30px;
    border-radius: 4px;
}}

QCheckBox {{
    spacing: 8px;
    color: {TEXT_PRIMARY};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {BORDER_COLOR};
    border-radius: 4px;
    background: {BG_INPUT};
}}

QCheckBox::indicator:checked {{
    background: {ACCENT_BLUE};
    border-color: {ACCENT_BLUE};
}}

QGroupBox {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: 600;
    color: {TEXT_PRIMARY};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 6px;
}}

QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    background: {BG_SECONDARY};
}}

QTabBar::tab {{
    background: {BG_PRIMARY};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER_COLOR};
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}

QTabBar::tab:selected {{
    background: {BG_SECONDARY};
    color: {ACCENT_BLUE};
    border-bottom-color: {BG_SECONDARY};
}}

QMenuBar {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
    border-bottom: 1px solid {BORDER_COLOR};
}}

QMenuBar::item:selected {{
    background-color: {HOVER_BG};
}}

QMenu {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
}}

QMenu::item:selected {{
    background-color: {SELECTED_BG};
}}

QStatusBar {{
    background-color: {BG_PRIMARY};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BORDER_COLOR};
    font-size: 12px;
}}

QToolTip {{
    background-color: {BG_SECONDARY};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 6px;
}}

QDialog {{
    background-color: {BG_PRIMARY};
}}

QFrame[class="card"] {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
}}

QFrame[class="sidebar"] {{
    background-color: {BG_SECONDARY};
    border-right: 1px solid {BORDER_COLOR};
}}

QFrame[class="separator"] {{
    background-color: {BORDER_COLOR};
    max-height: 1px;
}}
"""


def card_frame_style():
    return f"background-color: {BG_CARD}; border: 1px solid {BORDER_COLOR}; border-radius: 10px; padding: 16px;"


def sidebar_style():
    return f"background-color: {BG_SECONDARY}; border-right: 1px solid {BORDER_COLOR};"
