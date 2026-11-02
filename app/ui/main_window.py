"""Main application window with sidebar navigation."""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QFrame, QLabel, QButtonGroup, QStatusBar,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction

from app.ui.styles import (
    DARK_STYLESHEET, BG_SECONDARY, BORDER_COLOR, ACCENT_BLUE,
    TEXT_PRIMARY, TEXT_SECONDARY, sidebar_style,
)
from app.ui.dashboard import Dashboard
from app.ui.task_view import TaskView
from app.ui.calendar_view import CalendarView
from app.ui.weekly_review import WeeklyReview
from app.ui.notes import Notes
from app.ui.settings import Settings
from app.ui.catch_up import CatchUpDialog


NAV_ITEMS = [
    ("Dashboard", "dashboard"),
    ("Today's Task", "task"),
    ("Calendar", "calendar"),
    ("Weekly Review", "review"),
    ("Notes", "notes"),
    ("Settings", "settings"),
]


class MainWindow(QMainWindow):
    def __init__(self, db, scheduler=None):
        super().__init__()
        self.db = db
        self.scheduler = scheduler
        self.setWindowTitle("AI Security 90-Day Planner")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(DARK_STYLESHEET)
        self._build_ui()
        self._build_menu()
        self._navigate(0)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(sidebar_style())
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(4)

        # Logo
        logo = QLabel("AI Security\n90-Day Planner")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            font-size: 16px; font-weight: bold; color: {ACCENT_BLUE};
            padding: 16px 0 24px 0; background: transparent;
        """)
        sidebar_layout.addWidget(logo)

        # Nav buttons
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons = []

        for i, (label, key) in enumerate(NAV_ITEMS):
            btn = QPushButton(f"  {label}")
            btn.setProperty("class", "nav")
            btn.setCheckable(True)
            btn.setMinimumHeight(42)
            btn.clicked.connect(lambda checked, idx=i: self._navigate(idx))
            self._nav_group.addButton(btn, i)
            self._nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addSpacing(16)

        # Catch-up button
        catch_up_btn = QPushButton("  Catch Up")
        catch_up_btn.setProperty("class", "danger")
        catch_up_btn.setMinimumHeight(42)
        catch_up_btn.clicked.connect(self._show_catch_up)
        sidebar_layout.addWidget(catch_up_btn)

        sidebar_layout.addStretch()

        # Day indicator
        self._sidebar_day = QLabel("")
        self._sidebar_day.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sidebar_day.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; padding: 8px; background: transparent;")
        sidebar_layout.addWidget(self._sidebar_day)

        layout.addWidget(sidebar)

        # Content stack
        self._stack = QStackedWidget()

        self._dashboard = Dashboard(self.db)
        self._task_view = TaskView(self.db)
        self._calendar = CalendarView(self.db)
        self._weekly_review = WeeklyReview(self.db)
        self._notes = Notes(self.db)
        self._settings = Settings(self.db)

        self._stack.addWidget(self._dashboard)
        self._stack.addWidget(self._task_view)
        self._stack.addWidget(self._calendar)
        self._stack.addWidget(self._weekly_review)
        self._stack.addWidget(self._notes)
        self._stack.addWidget(self._settings)

        layout.addWidget(self._stack, 1)

        # Cross-widget signals
        self._task_view.status_changed.connect(self._on_status_changed)
        self._calendar.day_selected.connect(self._on_day_selected)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

    def _build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("File")
        backup_action = QAction("Backup Database...", self)
        backup_action.triggered.connect(lambda: (self._navigate(5), self._settings._backup()))
        file_menu.addAction(backup_action)

        export_action = QAction("Export JSON...", self)
        export_action.triggered.connect(lambda: (self._navigate(5), self._settings._export_json()))
        file_menu.addAction(export_action)

        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        nav_menu = menu.addMenu("Navigate")
        for i, (label, key) in enumerate(NAV_ITEMS):
            action = QAction(label, self)
            action.triggered.connect(lambda checked, idx=i: self._navigate(idx))
            nav_menu.addAction(action)

    def _navigate(self, index):
        self._nav_buttons[index].setChecked(True)
        self._stack.setCurrentIndex(index)
        widget = self._stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()
        self._update_sidebar_day()

    def _update_sidebar_day(self):
        today = self.db.get_today_day_number()
        if 1 <= today <= 90:
            self._sidebar_day.setText(f"Day {today} / 90")
        elif today > 90:
            self._sidebar_day.setText("Program Complete!")
        else:
            self._sidebar_day.setText("Not started yet")

    def _on_status_changed(self):
        current = self._stack.currentIndex()
        self._dashboard.refresh()
        if current != 1:
            widget = self._stack.widget(current)
            if hasattr(widget, "refresh"):
                widget.refresh()

    def _on_day_selected(self, day):
        self._task_view.show_day(day)
        self._navigate(1)

    def _show_catch_up(self):
        dialog = CatchUpDialog(self.db, self)
        dialog.exec()
        widget = self._stack.currentWidget()
        if hasattr(widget, "refresh"):
            widget.refresh()
        self._dashboard.refresh()
