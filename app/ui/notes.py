"""Notes view with search and per-day organization."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QTextEdit, QScrollArea, QLineEdit, QListWidget, QListWidgetItem,
    QSplitter, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from app.ui.styles import (
    BG_CARD, BG_INPUT, BORDER_COLOR, ACCENT_BLUE, ACCENT_CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    card_frame_style,
)


class Notes(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._current_day = None
        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(16)

        title = QLabel("Notes")
        title.setProperty("class", "heading")
        main.addWidget(title)

        # Search bar
        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search notes...")
        self._search_input.textChanged.connect(self._on_search)
        search_row.addWidget(self._search_input)
        main.addLayout(search_row)

        # Splitter: note list | editor
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: note list
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._note_list = QListWidget()
        self._note_list.currentRowChanged.connect(self._on_select)
        self._note_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {BORDER_COLOR};
            }}
            QListWidget::item:selected {{
                background-color: {ACCENT_BLUE};
                color: white;
            }}
        """)
        left_layout.addWidget(self._note_list)

        splitter.addWidget(left_frame)

        # Right: editor
        right_frame = QFrame()
        right_frame.setStyleSheet(card_frame_style())
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        self._editor_title = QLabel("Select a day to view notes")
        self._editor_title.setStyleSheet(f"font-size: 15px; font-weight: 600; background: transparent;")
        right_layout.addWidget(self._editor_title)

        self._tags_input = QLineEdit()
        self._tags_input.setPlaceholderText("Tags (comma separated)")
        right_layout.addWidget(self._tags_input)

        self._editor = QTextEdit()
        self._editor.setPlaceholderText("Write your notes here...")
        right_layout.addWidget(self._editor)

        save_btn = QPushButton("Save Notes")
        save_btn.setProperty("class", "primary")
        save_btn.clicked.connect(self._save)
        right_layout.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        splitter.addWidget(right_frame)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main.addWidget(splitter, 1)

    def refresh(self):
        self._load_list()

    def _load_list(self, filter_text=""):
        self._note_list.clear()
        if filter_text:
            notes = self.db.search_notes(filter_text)
        else:
            notes = self.db.get_all_notes()

        all_tasks = {t["day"]: t for t in self.db.get_all_tasks()}

        # Show all 90 days, highlight ones with notes
        if filter_text:
            for n in notes:
                day = n.get("day", 0)
                task = all_tasks.get(day, {})
                title = task.get("topic", f"Day {day}")
                preview = n.get("text", "")[:60]
                item = QListWidgetItem(f"Day {day}: {title}\n{preview}")
                item.setData(Qt.ItemDataRole.UserRole, day)
                self._note_list.addItem(item)
        else:
            days_with_notes = {n.get("day"): n for n in notes}
            for day in range(1, 91):
                task = all_tasks.get(day, {})
                title = task.get("topic", f"Day {day}")
                has_note = day in days_with_notes
                prefix = "[Note] " if has_note else ""
                item = QListWidgetItem(f"{prefix}Day {day}: {title}")
                item.setData(Qt.ItemDataRole.UserRole, day)
                if not has_note:
                    item.setForeground(QColor(TEXT_MUTED))
                self._note_list.addItem(item)

    def _on_search(self, text):
        self._load_list(text.strip())

    def _on_select(self, row):
        item = self._note_list.item(row)
        if not item:
            return
        day = item.data(Qt.ItemDataRole.UserRole)
        self._current_day = day
        task = self.db.get_task(day)
        title = task.get("topic", f"Day {day}") if task else f"Day {day}"
        self._editor_title.setText(f"Day {day}: {title}")

        note = self.db.get_note(day)
        self._editor.blockSignals(True)
        self._tags_input.blockSignals(True)
        self._editor.setPlainText(note.get("text", "") if note else "")
        self._tags_input.setText(note.get("tags", "") if note else "")
        self._editor.blockSignals(False)
        self._tags_input.blockSignals(False)

    def _save(self):
        if self._current_day:
            self.db.save_note(
                self._current_day,
                self._editor.toPlainText(),
                self._tags_input.text(),
            )
            self._load_list(self._search_input.text().strip())

    def show_day(self, day):
        for i in range(self._note_list.count()):
            item = self._note_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == day:
                self._note_list.setCurrentRow(i)
                break
