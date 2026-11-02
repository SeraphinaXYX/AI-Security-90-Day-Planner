"""Today's task view with status controls, resources, and notes."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QTextEdit, QScrollArea, QSizePolicy, QGridLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl

from app.ui.styles import (
    BG_CARD, BG_INPUT, BORDER_COLOR, ACCENT_BLUE, ACCENT_CYAN,
    ACCENT_PURPLE, STATUS_COMPLETED, STATUS_PENDING, STATUS_OVERDUE,
    STATUS_SKIPPED, STATUS_POSTPONED, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_MUTED, card_frame_style,
)


class ResourceLink(QPushButton):
    def __init__(self, text, url, parent=None):
        super().__init__(f"  {text}", parent)
        self._url = url
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT_CYAN};
                border: none;
                text-align: left;
                font-size: 13px;
                padding: 4px 0;
            }}
            QPushButton:hover {{
                color: {ACCENT_BLUE};
                text-decoration: underline;
            }}
        """)
        self.clicked.connect(self._open)

    def _open(self):
        QDesktopServices.openUrl(QUrl(self._url))


class TaskView(QWidget):
    status_changed = Signal()
    navigate_to_day = Signal(int)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._current_day = None
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self._main = QVBoxLayout(container)
        self._main.setContentsMargins(24, 24, 24, 24)
        self._main.setSpacing(16)

        # Navigation row
        nav_row = QHBoxLayout()
        self._prev_btn = QPushButton("< Previous Day")
        self._prev_btn.clicked.connect(lambda: self._navigate(-1))
        self._next_btn = QPushButton("Next Day >")
        self._next_btn.clicked.connect(lambda: self._navigate(1))
        self._today_btn = QPushButton("Go to Today")
        self._today_btn.setProperty("class", "primary")
        self._today_btn.clicked.connect(self._go_today)
        nav_row.addWidget(self._prev_btn)
        nav_row.addStretch()
        nav_row.addWidget(self._today_btn)
        nav_row.addStretch()
        nav_row.addWidget(self._next_btn)
        self._main.addLayout(nav_row)

        # Day header
        self._day_title = QLabel("")
        self._day_title.setProperty("class", "heading")
        self._main.addWidget(self._day_title)

        self._phase_label = QLabel("")
        self._phase_label.setProperty("class", "phase-label")
        self._main.addWidget(self._phase_label)

        # Task info card
        info_frame = QFrame()
        info_frame.setStyleSheet(card_frame_style())
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 16, 20, 16)
        info_layout.setSpacing(12)

        self._task_title = QLabel("")
        self._task_title.setStyleSheet(f"font-size: 18px; font-weight: 600; color: {TEXT_PRIMARY}; background: transparent;")
        self._task_title.setWordWrap(True)
        info_layout.addWidget(self._task_title)

        # Concepts
        self._concepts_label = QLabel("")
        self._concepts_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        self._concepts_label.setWordWrap(True)
        info_layout.addWidget(self._concepts_label)

        # Exercise
        exercise_header = QLabel("Exercise")
        exercise_header.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {ACCENT_CYAN}; background: transparent; margin-top: 8px;")
        info_layout.addWidget(exercise_header)

        self._task_desc = QLabel("")
        self._task_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.5; background: transparent;")
        self._task_desc.setWordWrap(True)
        info_layout.addWidget(self._task_desc)

        # Deliverable
        self._deliverable_label = QLabel("")
        self._deliverable_label.setStyleSheet(f"color: {ACCENT_BLUE}; font-size: 13px; background: transparent; margin-top: 4px;")
        self._deliverable_label.setWordWrap(True)
        info_layout.addWidget(self._deliverable_label)

        # Reflection prompt
        self._reflection_label = QLabel("")
        self._reflection_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic; background: transparent;")
        self._reflection_label.setWordWrap(True)
        info_layout.addWidget(self._reflection_label)

        # Phase badge + duration row
        meta_row = QHBoxLayout()
        self._difficulty_label = QLabel("")
        self._difficulty_label.setStyleSheet(f"""
            background-color: {ACCENT_PURPLE}; color: white;
            padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;
        """)
        self._duration_label = QLabel("")
        self._duration_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        meta_row.addWidget(self._difficulty_label)
        meta_row.addWidget(self._duration_label)
        meta_row.addStretch()
        info_layout.addLayout(meta_row)

        self._main.addWidget(info_frame)

        # Status buttons
        status_frame = QFrame()
        status_frame.setStyleSheet(card_frame_style())
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(20, 16, 20, 16)

        status_title = QLabel("Status")
        status_title.setStyleSheet(f"font-size: 14px; font-weight: 600; background: transparent;")
        status_layout.addWidget(status_title)

        self._status_label = QLabel("pending")
        self._status_label.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY}; background: transparent;")
        status_layout.addWidget(self._status_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._btn_complete = QPushButton("Mark Complete")
        self._btn_complete.setProperty("class", "success")
        self._btn_complete.clicked.connect(lambda: self._set_status("completed"))

        self._btn_skip = QPushButton("Skip")
        self._btn_skip.setProperty("class", "warning")
        self._btn_skip.clicked.connect(lambda: self._set_status("skipped"))

        self._btn_postpone = QPushButton("Postpone")
        self._btn_postpone.setProperty("class", "danger")
        self._btn_postpone.clicked.connect(lambda: self._set_status("postponed"))

        self._btn_reset = QPushButton("Reset to Pending")
        self._btn_reset.clicked.connect(lambda: self._set_status("pending"))

        btn_row.addWidget(self._btn_complete)
        btn_row.addWidget(self._btn_skip)
        btn_row.addWidget(self._btn_postpone)
        btn_row.addWidget(self._btn_reset)
        status_layout.addLayout(btn_row)

        self._main.addWidget(status_frame)

        # Resources
        res_frame = QFrame()
        res_frame.setStyleSheet(card_frame_style())
        res_layout = QVBoxLayout(res_frame)
        res_layout.setContentsMargins(20, 16, 20, 16)

        res_title = QLabel("Resources")
        res_title.setStyleSheet(f"font-size: 14px; font-weight: 600; background: transparent;")
        res_layout.addWidget(res_title)

        self._resources_container = QVBoxLayout()
        res_layout.addLayout(self._resources_container)

        self._main.addWidget(res_frame)

        # Notes
        notes_frame = QFrame()
        notes_frame.setStyleSheet(card_frame_style())
        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setContentsMargins(20, 16, 20, 16)

        notes_title = QLabel("Notes for this day")
        notes_title.setStyleSheet(f"font-size: 14px; font-weight: 600; background: transparent;")
        notes_layout.addWidget(notes_title)

        self._notes_edit = QTextEdit()
        self._notes_edit.setPlaceholderText("Write your notes here...")
        self._notes_edit.setMinimumHeight(120)
        notes_layout.addWidget(self._notes_edit)

        save_btn = QPushButton("Save Notes")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._save_notes)
        notes_layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self._main.addWidget(notes_frame)

        self._main.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def show_day(self, day):
        self._current_day = max(1, min(90, day))
        self.refresh()

    def _navigate(self, delta):
        if self._current_day is not None:
            new_day = self._current_day + delta
            if 1 <= new_day <= 90:
                self.show_day(new_day)
                self.navigate_to_day.emit(new_day)

    def _go_today(self):
        today = self.db.get_today_day_number()
        today = max(1, min(90, today))
        self.show_day(today)
        self.navigate_to_day.emit(today)

    def refresh(self):
        if self._current_day is None:
            self._current_day = max(1, min(90, self.db.get_today_day_number()))

        day = self._current_day
        task = self.db.get_task(day)
        if not task:
            self._day_title.setText(f"Day {day}")
            self._task_title.setText("No task data")
            return

        self._day_title.setText(f"Day {day} / 90")
        self._phase_label.setText(f"PHASE {task.get('phase', '?')}: {task.get('phase_name', '')}")
        self._task_title.setText(task.get("topic", ""))

        concepts = task.get("concepts", [])
        if concepts:
            self._concepts_label.setText("Key concepts: " + "  •  ".join(concepts))
            self._concepts_label.setVisible(True)
        else:
            self._concepts_label.setVisible(False)

        self._task_desc.setText(task.get("exercise", ""))

        deliverable = task.get("deliverable", "")
        if deliverable:
            self._deliverable_label.setText(f"Deliverable: {deliverable}")
            self._deliverable_label.setVisible(True)
        else:
            self._deliverable_label.setVisible(False)

        reflection = task.get("reflection_prompt", "")
        if reflection:
            self._reflection_label.setText(f"Reflect: {reflection}")
            self._reflection_label.setVisible(True)
        else:
            self._reflection_label.setVisible(False)

        phase = task.get("phase", 1)
        phase_labels = {1: "FOUNDATIONS", 2: "AI/LLM", 3: "RED TEAM", 4: "PROJECT", 5: "CAREER"}
        self._difficulty_label.setText(phase_labels.get(phase, ""))
        mins = task.get("estimated_minutes", 60)
        self._duration_label.setText(f"  ~{mins} min")

        status = task.get("status", "pending")
        today_num = self.db.get_today_day_number()
        if status == "pending" and day < today_num:
            status = "overdue"

        color_map = {
            "completed": STATUS_COMPLETED,
            "pending": STATUS_PENDING,
            "skipped": STATUS_SKIPPED,
            "postponed": STATUS_POSTPONED,
            "overdue": STATUS_OVERDUE,
        }
        color = color_map.get(status, TEXT_SECONDARY)
        self._status_label.setText(f"Status: {status.upper()}")
        self._status_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {color}; background: transparent;")

        self._prev_btn.setEnabled(day > 1)
        self._next_btn.setEnabled(day < 90)

        # Resources
        while self._resources_container.count():
            item = self._resources_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        resources = task.get("resources", [])
        if resources:
            for r in resources:
                if isinstance(r, dict):
                    link = ResourceLink(r.get("title", r.get("url", "")), r.get("url", ""))
                elif isinstance(r, str):
                    link = ResourceLink(r, r)
                else:
                    continue
                self._resources_container.addWidget(link)
        else:
            no_res = QLabel("No resources for this day")
            no_res.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
            self._resources_container.addWidget(no_res)

        # Notes
        note = self.db.get_note(day)
        self._notes_edit.blockSignals(True)
        self._notes_edit.setPlainText(note.get("text", "") if note else "")
        self._notes_edit.blockSignals(False)

    def _set_status(self, status):
        if self._current_day:
            self.db.update_task_status(self._current_day, status)
            self.refresh()
            self.status_changed.emit()

    def _save_notes(self):
        if self._current_day:
            text = self._notes_edit.toPlainText()
            self.db.save_note(self._current_day, text, "")
