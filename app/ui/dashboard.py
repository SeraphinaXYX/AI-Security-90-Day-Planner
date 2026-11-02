"""Dashboard widget showing progress overview."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QFrame, QGridLayout, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor, QFont

from app.ui.styles import (
    BG_CARD, BORDER_COLOR, ACCENT_BLUE, ACCENT_CYAN, ACCENT_PURPLE,
    STATUS_COMPLETED, STATUS_PENDING, STATUS_OVERDUE, STATUS_SKIPPED,
    STATUS_POSTPONED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    card_frame_style,
)


class StatCard(QFrame):
    def __init__(self, title, value="0", color=ACCENT_BLUE, parent=None):
        super().__init__(parent)
        self.setStyleSheet(card_frame_style())
        self.setMinimumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self._title = QLabel(title)
        self._title.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 500; background: transparent;")

        self._value = QLabel(str(value))
        self._value.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold; background: transparent;")

        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addStretch()

    def set_value(self, value):
        self._value.setText(str(value))


class PhaseProgressBar(QFrame):
    def __init__(self, phase_num, phase_name, completed, total, parent=None):
        super().__init__(parent)
        self.setStyleSheet(card_frame_style())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        header = QHBoxLayout()
        lbl = QLabel(f"Phase {phase_num}: {phase_name}")
        lbl.setStyleSheet(f"font-weight: 600; font-size: 13px; background: transparent;")
        count_lbl = QLabel(f"{completed}/{total}")
        count_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; font-weight: bold; background: transparent;")
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(count_lbl)
        layout.addLayout(header)

        bar = QProgressBar()
        bar.setRange(0, max(total, 1))
        bar.setValue(completed)
        bar.setFixedHeight(10)
        bar.setTextVisible(False)
        layout.addWidget(bar)


class WeeklyBarChart(QWidget):
    """Simple bar chart drawn with QPainter."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self.setMinimumHeight(160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, data):
        self._data = data
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin_bottom = 28
        margin_top = 10
        chart_h = h - margin_bottom - margin_top

        max_val = max((d["total"] for d in self._data), default=1) or 1
        bar_w = max(12, min(40, (w - 20) // len(self._data) - 8))
        gap = (w - bar_w * len(self._data)) / (len(self._data) + 1)

        for i, d in enumerate(self._data):
            x = gap + i * (bar_w + gap)

            # Background bar (total)
            total_h = int(d["total"] / max_val * chart_h)
            painter.setBrush(QColor(BORDER_COLOR))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(x), margin_top + chart_h - total_h, bar_w, total_h, 4, 4)

            # Completed bar
            comp_h = int(d["completed"] / max_val * chart_h)
            painter.setBrush(QColor(STATUS_COMPLETED))
            painter.drawRoundedRect(int(x), margin_top + chart_h - comp_h, bar_w, comp_h, 4, 4)

            # Week label
            painter.setPen(QColor(TEXT_MUTED))
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(int(x), h - 4, f"W{d['week']}")

        painter.end()


class Dashboard(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(24, 24, 24, 24)
        self._layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("Dashboard")
        title.setProperty("class", "heading")
        self._day_label = QLabel("")
        self._day_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; background: transparent;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._day_label)
        self._layout.addLayout(header)

        # Overall progress
        prog_frame = QFrame()
        prog_frame.setStyleSheet(card_frame_style())
        prog_layout = QVBoxLayout(prog_frame)
        prog_layout.setContentsMargins(16, 12, 16, 12)

        prog_header = QHBoxLayout()
        prog_title = QLabel("Overall Progress")
        prog_title.setStyleSheet("font-size: 15px; font-weight: 600; background: transparent;")
        self._prog_pct = QLabel("0%")
        self._prog_pct.setStyleSheet(f"color: {ACCENT_BLUE}; font-size: 18px; font-weight: bold; background: transparent;")
        prog_header.addWidget(prog_title)
        prog_header.addStretch()
        prog_header.addWidget(self._prog_pct)
        prog_layout.addLayout(prog_header)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 90)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(18)
        prog_layout.addWidget(self._progress_bar)

        self._layout.addWidget(prog_frame)

        # Stats cards row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        self._stat_completed = StatCard("Completed", "0", STATUS_COMPLETED)
        self._stat_pending = StatCard("Pending", "0", STATUS_PENDING)
        self._stat_postponed = StatCard("Postponed", "0", STATUS_POSTPONED)
        self._stat_skipped = StatCard("Skipped", "0", STATUS_SKIPPED)
        self._stat_streak = StatCard("Current Streak", "0", ACCENT_PURPLE)
        stats_row.addWidget(self._stat_completed)
        stats_row.addWidget(self._stat_pending)
        stats_row.addWidget(self._stat_postponed)
        stats_row.addWidget(self._stat_skipped)
        stats_row.addWidget(self._stat_streak)
        self._layout.addLayout(stats_row)

        # Weekly chart
        chart_frame = QFrame()
        chart_frame.setStyleSheet(card_frame_style())
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(16, 12, 16, 12)
        chart_title = QLabel("Weekly Progress")
        chart_title.setStyleSheet("font-size: 15px; font-weight: 600; background: transparent;")
        chart_layout.addWidget(chart_title)
        self._weekly_chart = WeeklyBarChart()
        chart_layout.addWidget(self._weekly_chart)
        self._layout.addWidget(chart_frame)

        # Phase progress
        phase_title = QLabel("Phase Progress")
        phase_title.setStyleSheet("font-size: 15px; font-weight: 600; background: transparent;")
        self._layout.addWidget(phase_title)

        self._phase_container = QVBoxLayout()
        self._phase_container.setSpacing(8)
        self._layout.addLayout(self._phase_container)

        self._layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        today = self.db.get_today_day_number()
        if 1 <= today <= 90:
            task = self.db.get_task(today)
            topic = task.get("topic", "") if task else ""
            self._day_label.setText(f"Day {today} / 90  ·  {topic}")
        elif today > 90:
            self._day_label.setText("Program completed!")
        else:
            self._day_label.setText("Program starts when you launch for the first time")

        stats = self.db.get_progress_stats()
        completed = stats.get("completed", 0)
        self._progress_bar.setValue(completed)
        pct = int(completed / 90 * 100) if completed else 0
        self._prog_pct.setText(f"{pct}%")

        self._stat_completed.set_value(completed)
        self._stat_pending.set_value(stats.get("pending", 0))
        self._stat_postponed.set_value(stats.get("postponed", 0))
        self._stat_skipped.set_value(stats.get("skipped", 0))
        self._stat_streak.set_value(self.db.get_streak())

        # Weekly data
        weekly = []
        for w in range(1, 14):
            start = (w - 1) * 7 + 1
            end = min(w * 7, 90)
            tasks = self.db.get_tasks_in_range(start, end)
            total = len(tasks)
            comp = sum(1 for t in tasks if t.get("status") == "completed")
            weekly.append({"week": w, "total": total, "completed": comp})
        self._weekly_chart.set_data(weekly)

        # Phase breakdown
        while self._phase_container.count():
            item = self._phase_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        phases = [
            (1, "Security & Engineering Foundations", 1, 20),
            (2, "AI Engineering & LLM Agents", 21, 40),
            (3, "AI Security & Red Teaming", 41, 60),
            (4, "Portfolio Research Project", 61, 80),
            (5, "Research & Internship Prep", 81, 90),
        ]
        for pnum, pname, start, end in phases:
            tasks = self.db.get_tasks_in_range(start, end)
            total = len(tasks)
            comp = sum(1 for t in tasks if t.get("status") == "completed")
            bar = PhaseProgressBar(pnum, pname, comp, total)
            self._phase_container.addWidget(bar)
