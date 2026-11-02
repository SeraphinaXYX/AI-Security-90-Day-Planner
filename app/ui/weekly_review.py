"""Weekly review widget with reflection areas."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QTextEdit, QScrollArea, QComboBox, QProgressBar,
)
from PySide6.QtCore import Qt

from app.ui.styles import (
    ACCENT_BLUE, ACCENT_CYAN, STATUS_COMPLETED, STATUS_PENDING,
    STATUS_SKIPPED, STATUS_POSTPONED, STATUS_OVERDUE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    card_frame_style,
)


class WeeklyReview(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._current_week = 1
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main = QVBoxLayout(container)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(16)

        title = QLabel("Weekly Review")
        title.setProperty("class", "heading")
        main.addWidget(title)

        # Week selector
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Select Week:"))
        self._week_combo = QComboBox()
        for w in range(1, 14):
            start = (w - 1) * 7 + 1
            end = min(w * 7, 90)
            self._week_combo.addItem(f"Week {w} (Day {start}-{end})", w)
        self._week_combo.currentIndexChanged.connect(self._on_week_changed)
        sel_row.addWidget(self._week_combo)
        sel_row.addStretch()
        main.addLayout(sel_row)

        # Week summary card
        summary_frame = QFrame()
        summary_frame.setStyleSheet(card_frame_style())
        summary_layout = QVBoxLayout(summary_frame)
        summary_layout.setContentsMargins(20, 16, 20, 16)
        summary_layout.setSpacing(12)

        summary_title = QLabel("Week Summary")
        summary_title.setStyleSheet(f"font-size: 15px; font-weight: 600; background: transparent;")
        summary_layout.addWidget(summary_title)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(14)
        self._progress_bar.setTextVisible(False)
        summary_layout.addWidget(self._progress_bar)

        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        self._stats_label.setWordWrap(True)
        summary_layout.addWidget(self._stats_label)

        # Task list for the week
        self._task_list_label = QLabel("")
        self._task_list_label.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; background: transparent;")
        self._task_list_label.setWordWrap(True)
        summary_layout.addWidget(self._task_list_label)

        main.addWidget(summary_frame)

        # Reflection
        ref_frame = QFrame()
        ref_frame.setStyleSheet(card_frame_style())
        ref_layout = QVBoxLayout(ref_frame)
        ref_layout.setContentsMargins(20, 16, 20, 16)
        ref_layout.setSpacing(12)

        ref_title = QLabel("Reflection")
        ref_title.setStyleSheet(f"font-size: 15px; font-weight: 600; background: transparent;")
        ref_layout.addWidget(ref_title)

        ref_layout.addWidget(QLabel("What went well? What was challenging? What would you do differently?"))

        self._reflection_edit = QTextEdit()
        self._reflection_edit.setPlaceholderText("Write your weekly reflection here...")
        self._reflection_edit.setMinimumHeight(120)
        ref_layout.addWidget(self._reflection_edit)

        main.addWidget(ref_frame)

        # Key learnings
        learn_frame = QFrame()
        learn_frame.setStyleSheet(card_frame_style())
        learn_layout = QVBoxLayout(learn_frame)
        learn_layout.setContentsMargins(20, 16, 20, 16)
        learn_layout.setSpacing(12)

        learn_title = QLabel("Key Learnings")
        learn_title.setStyleSheet(f"font-size: 15px; font-weight: 600; background: transparent;")
        learn_layout.addWidget(learn_title)

        learn_layout.addWidget(QLabel("List the most important things you learned this week:"))

        self._learnings_edit = QTextEdit()
        self._learnings_edit.setPlaceholderText("- Learning 1\n- Learning 2\n- ...")
        self._learnings_edit.setMinimumHeight(100)
        learn_layout.addWidget(self._learnings_edit)

        main.addWidget(learn_frame)

        # Save button
        save_btn = QPushButton("Save Weekly Review")
        save_btn.setProperty("class", "primary")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self._save)
        main.addWidget(save_btn)

        main.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _on_week_changed(self, index):
        self._current_week = self._week_combo.currentData()
        self.refresh()

    def refresh(self):
        week = self._current_week
        start = (week - 1) * 7 + 1
        end = min(week * 7, 90)

        tasks = self.db.get_tasks_in_range(start, end)
        total = len(tasks)
        today_num = self.db.get_today_day_number()

        completed = sum(1 for t in tasks if t.get("status") == "completed")
        skipped = sum(1 for t in tasks if t.get("status") == "skipped")
        postponed = sum(1 for t in tasks if t.get("status") == "postponed")
        pending = total - completed - skipped - postponed

        self._progress_bar.setRange(0, max(total, 1))
        self._progress_bar.setValue(completed)

        parts = [f"{completed}/{total} completed"]
        if skipped:
            parts.append(f"{skipped} skipped")
        if postponed:
            parts.append(f"{postponed} postponed")
        if pending:
            parts.append(f"{pending} pending")
        self._stats_label.setText("  |  ".join(parts))

        # Task list
        lines = []
        for t in tasks:
            status = t.get("status", "pending")
            if status == "pending" and t.get("day", 0) < today_num:
                status = "overdue"
            icon = {"completed": "[Done]", "skipped": "[Skip]", "postponed": "[Later]",
                    "overdue": "[!]", "pending": "[ ]"}.get(status, "[ ]")
            lines.append(f"{icon}  Day {t.get('day', '?')}: {t.get('topic', '')}")
        self._task_list_label.setText("\n".join(lines))

        # Load existing review
        review = self.db.get_weekly_review(week)
        self._reflection_edit.blockSignals(True)
        self._learnings_edit.blockSignals(True)
        self._reflection_edit.setPlainText(review.get("reflection", "") if review else "")
        self._learnings_edit.setPlainText(review.get("learnings", "") if review else "")
        self._reflection_edit.blockSignals(False)
        self._learnings_edit.blockSignals(False)

    def _save(self):
        self.db.save_weekly_review(
            self._current_week,
            self._reflection_edit.toPlainText(),
            self._learnings_edit.toPlainText(),
        )
