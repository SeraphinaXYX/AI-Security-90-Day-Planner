"""Catch-up dialog for rescheduling overdue tasks."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QCheckBox, QComboBox, QMessageBox,
)
from PySide6.QtCore import Qt

from app.ui.styles import (
    BG_CARD, BORDER_COLOR, ACCENT_BLUE, STATUS_OVERDUE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    card_frame_style,
)


class CatchUpDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Catch Up - Overdue Tasks")
        self.setMinimumSize(600, 500)
        self._build_ui()
        self._load_overdue()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(16)

        title = QLabel("Overdue Tasks")
        title.setProperty("class", "heading")
        main.addWidget(title)

        desc = QLabel(
            "The following tasks are past their scheduled day and still pending. "
            "Choose what to do with each one:"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        main.addWidget(desc)

        # Bulk actions
        bulk_row = QHBoxLayout()
        mark_all_done = QPushButton("Mark All Complete")
        mark_all_done.setProperty("class", "success")
        mark_all_done.clicked.connect(self._mark_all_complete)

        skip_all = QPushButton("Skip All")
        skip_all.setProperty("class", "warning")
        skip_all.clicked.connect(self._skip_all)

        bulk_row.addWidget(mark_all_done)
        bulk_row.addWidget(skip_all)
        bulk_row.addStretch()
        main.addLayout(bulk_row)

        # Scrollable task list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._list_widget = QFrame()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)

        scroll.setWidget(self._list_widget)
        main.addWidget(scroll, 1)

        # Close
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        main.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _load_overdue(self):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        today_num = self.db.get_today_day_number()
        self._overdue_tasks = []

        for task in self.db.get_all_tasks():
            if task.get("status") == "pending" and task.get("day", 0) < today_num:
                self._overdue_tasks.append(task)

        if not self._overdue_tasks:
            no_lbl = QLabel("No overdue tasks! You're all caught up.")
            no_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; padding: 20px; background: transparent;")
            no_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list_layout.addWidget(no_lbl)
            return

        self._task_rows = []
        for task in self._overdue_tasks:
            row = self._make_task_row(task)
            self._task_rows.append(row)
            self._list_layout.addWidget(row["frame"])

        self._list_layout.addStretch()

    def _make_task_row(self, task):
        frame = QFrame()
        frame.setStyleSheet(card_frame_style())
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)

        day = task.get("day", 0)
        info = QVBoxLayout()
        day_lbl = QLabel(f"Day {day}")
        day_lbl.setStyleSheet(f"font-weight: bold; color: {STATUS_OVERDUE}; background: transparent;")
        title_lbl = QLabel(task.get("topic", ""))
        title_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        title_lbl.setWordWrap(True)
        info.addWidget(day_lbl)
        info.addWidget(title_lbl)
        layout.addLayout(info, 1)

        # Action combo
        combo = QComboBox()
        combo.addItem("Keep Pending", "pending")
        combo.addItem("Mark Complete", "completed")
        combo.addItem("Skip", "skipped")
        combo.addItem("Postpone", "postponed")
        layout.addWidget(combo)

        apply_btn = QPushButton("Apply")
        apply_btn.setProperty("class", "primary")
        apply_btn.clicked.connect(lambda: self._apply_single(day, combo, frame))
        layout.addWidget(apply_btn)

        return {"frame": frame, "day": day, "combo": combo}

    def _apply_single(self, day, combo, frame):
        status = combo.currentData()
        if status != "pending":
            self.db.update_task_status(day, status)
            frame.setVisible(False)

    def _mark_all_complete(self):
        for task in self._overdue_tasks:
            self.db.update_task_status(task["day"], "completed")
        self._load_overdue()

    def _skip_all(self):
        for task in self._overdue_tasks:
            self.db.update_task_status(task["day"], "skipped")
        self._load_overdue()
