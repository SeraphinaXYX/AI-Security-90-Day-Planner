"""Calendar view showing all 90 days color-coded by status."""
from datetime import date, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QPushButton, QFrame, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from app.ui.styles import (
    BG_CARD, BG_INPUT, BORDER_COLOR, ACCENT_BLUE,
    STATUS_COMPLETED, STATUS_PENDING, STATUS_OVERDUE,
    STATUS_SKIPPED, STATUS_POSTPONED, STATUS_TODAY,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    card_frame_style,
)


STATUS_COLORS = {
    "completed": STATUS_COMPLETED,
    "pending": STATUS_PENDING,
    "skipped": STATUS_SKIPPED,
    "postponed": STATUS_POSTPONED,
    "overdue": STATUS_OVERDUE,
    "today": STATUS_TODAY,
    "future": BG_INPUT,
}


class DayCell(QPushButton):
    day_clicked = Signal(int)

    def __init__(self, day_num, status, is_today=False, parent=None):
        super().__init__(parent)
        self.day_num = day_num
        self.setFixedSize(60, 60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(str(day_num))
        self.clicked.connect(lambda: self.day_clicked.emit(self.day_num))

        if is_today:
            color = STATUS_COLORS["today"]
            border = f"3px solid {ACCENT_BLUE}"
        else:
            color = STATUS_COLORS.get(status, STATUS_COLORS["future"])
            border = f"1px solid {BORDER_COLOR}"

        text_color = "white" if status == "completed" or is_today else TEXT_PRIMARY
        bg = color if status in ("completed", "today") or is_today else BG_CARD

        if status == "completed":
            bg = STATUS_COMPLETED
        elif status == "skipped":
            bg = STATUS_SKIPPED
        elif status == "postponed":
            bg = STATUS_POSTPONED
        elif is_today:
            bg = ACCENT_BLUE
        elif status == "overdue":
            bg = STATUS_OVERDUE

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {text_color};
                border: {border};
                border-radius: 8px;
                font-size: 14px;
                font-weight: {'bold' if is_today else 'normal'};
            }}
            QPushButton:hover {{
                border-color: {ACCENT_BLUE};
                border-width: 2px;
            }}
        """)


class CalendarView(QWidget):
    day_selected = Signal(int)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        title = QLabel("Calendar")
        title.setProperty("class", "heading")
        main_layout.addWidget(title)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)
        legend_items = [
            ("Today", STATUS_TODAY),
            ("Completed", STATUS_COMPLETED),
            ("Pending", STATUS_PENDING),
            ("Postponed", STATUS_POSTPONED),
            ("Skipped", STATUS_SKIPPED),
            ("Overdue", STATUS_OVERDUE),
        ]
        for name, color in legend_items:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 14px; background: transparent;")
            lbl = QLabel(name)
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;")
            legend_layout.addWidget(dot)
            legend_layout.addWidget(lbl)
        legend_layout.addStretch()
        main_layout.addLayout(legend_layout)

        # Month containers
        self._months_layout = QVBoxLayout()
        self._months_layout.setSpacing(24)
        main_layout.addLayout(self._months_layout)

        main_layout.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        while self._months_layout.count():
            item = self._months_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        start_date_str = self.db.get_start_date()
        try:
            start_date = date.fromisoformat(start_date_str)
        except (ValueError, TypeError):
            start_date = date.today()

        today_num = self.db.get_today_day_number()
        all_tasks = {t["day"]: t for t in self.db.get_all_tasks()}

        # Group days by calendar month
        months = {}
        for d in range(1, 91):
            dt = start_date + timedelta(days=d - 1)
            key = (dt.year, dt.month)
            if key not in months:
                months[key] = []
            task = all_tasks.get(d, {})
            status = task.get("status", "pending")
            if status == "pending" and d < today_num:
                status = "overdue"
            months[key].append((d, dt, status, d == today_num))

        for (year, month), days in sorted(months.items()):
            month_frame = QFrame()
            month_frame.setStyleSheet(card_frame_style())
            month_layout = QVBoxLayout(month_frame)
            month_layout.setContentsMargins(16, 12, 16, 16)

            month_name = date(year, month, 1).strftime("%B %Y")
            month_lbl = QLabel(month_name)
            month_lbl.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {TEXT_PRIMARY}; background: transparent;")
            month_layout.addWidget(month_lbl)

            # Day headers
            header_layout = QGridLayout()
            header_layout.setSpacing(6)
            for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
                lbl = QLabel(name)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; font-weight: bold; background: transparent;")
                header_layout.addWidget(lbl, 0, i)

            # Fill grid
            first_dt = days[0][1]
            start_col = first_dt.weekday()
            row = 1
            col = start_col
            for day_num, dt, status, is_today in days:
                cell = DayCell(day_num, status, is_today)
                cell.day_clicked.connect(self.day_selected.emit)
                header_layout.addWidget(cell, row, col, Qt.AlignmentFlag.AlignCenter)
                col += 1
                if col > 6:
                    col = 0
                    row += 1

            month_layout.addLayout(header_layout)
            self._months_layout.addWidget(month_frame)
