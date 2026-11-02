"""Settings view: reminders, backup, about."""
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QScrollArea, QTimeEdit, QCheckBox, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout,
)
from PySide6.QtCore import Qt, QTime

from app.config import APP_VERSION
from app.ui.styles import (
    ACCENT_BLUE, TEXT_SECONDARY, TEXT_MUTED, card_frame_style,
)


class Settings(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main = QVBoxLayout(container)
        main.setContentsMargins(24, 24, 24, 24)
        main.setSpacing(20)

        title = QLabel("Settings")
        title.setProperty("class", "heading")
        main.addWidget(title)

        # ── Reminders ──────────────────────────
        rem_group = QGroupBox("Daily Reminders")
        rem_layout = QVBoxLayout(rem_group)
        rem_layout.setSpacing(12)

        self._reminders_enabled = QCheckBox("Enable all reminders")
        rem_layout.addWidget(self._reminders_enabled)

        form = QFormLayout()
        form.setSpacing(10)

        self._morning_cb = QCheckBox("Morning reminder")
        self._morning_time = QTimeEdit()
        self._morning_time.setDisplayFormat("HH:mm")
        row_m = QHBoxLayout()
        row_m.addWidget(self._morning_cb)
        row_m.addWidget(self._morning_time)
        row_m.addStretch()
        form.addRow(row_m)

        self._evening_cb = QCheckBox("Evening reminder")
        self._evening_time = QTimeEdit()
        self._evening_time.setDisplayFormat("HH:mm")
        row_e = QHBoxLayout()
        row_e.addWidget(self._evening_cb)
        row_e.addWidget(self._evening_time)
        row_e.addStretch()
        form.addRow(row_e)

        self._night_cb = QCheckBox("Night check")
        self._night_time = QTimeEdit()
        self._night_time.setDisplayFormat("HH:mm")
        row_n = QHBoxLayout()
        row_n.addWidget(self._night_cb)
        row_n.addWidget(self._night_time)
        row_n.addStretch()
        form.addRow(row_n)

        rem_layout.addLayout(form)

        save_rem_btn = QPushButton("Save Reminder Settings")
        save_rem_btn.setProperty("class", "primary")
        save_rem_btn.clicked.connect(self._save_reminders)
        rem_layout.addWidget(save_rem_btn, alignment=Qt.AlignmentFlag.AlignRight)

        main.addWidget(rem_group)

        # ── Data Management ────────────────────
        backup_group = QGroupBox("Data Management")
        backup_layout = QVBoxLayout(backup_group)
        backup_layout.setSpacing(12)

        btn_row = QHBoxLayout()
        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self._backup)
        btn_row.addWidget(backup_btn)

        export_btn = QPushButton("Export as JSON")
        export_btn.clicked.connect(self._export_json)
        btn_row.addWidget(export_btn)
        btn_row.addStretch()
        backup_layout.addLayout(btn_row)

        note = QLabel("Backups are saved to data/backups/. JSON export includes all tasks, notes, and reviews.")
        note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        note.setWordWrap(True)
        backup_layout.addWidget(note)

        main.addWidget(backup_group)

        # ── About ──────────────────────────────
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout(about_group)
        about_layout.addWidget(QLabel(f"AI Security 90-Day Learning Planner  v{APP_VERSION}"))
        self._start_label = QLabel("Start date: —")
        self._start_label.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        about_layout.addWidget(self._start_label)

        about_text = QLabel(
            "Phases: Foundations → AI/LLM → Red Teaming → Portfolio → Career Prep\n"
            "Built with PySide6 + SQLite"
        )
        about_text.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)

        main.addWidget(about_group)
        main.addStretch()
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def refresh(self):
        self._reminders_enabled.setChecked(self.db.get_config("reminders_enabled", "true") == "true")
        self._morning_cb.setChecked(self.db.get_config("reminder_morning_enabled", "true") == "true")
        self._evening_cb.setChecked(self.db.get_config("reminder_evening_enabled", "true") == "true")
        self._night_cb.setChecked(self.db.get_config("reminder_night_enabled", "true") == "true")
        self._morning_time.setTime(_parse_qtime(self.db.get_config("reminder_morning", "09:00")))
        self._evening_time.setTime(_parse_qtime(self.db.get_config("reminder_evening", "19:00")))
        self._night_time.setTime(_parse_qtime(self.db.get_config("reminder_night", "22:00")))
        self._start_label.setText(f"Start date: {self.db.get_start_date()}")

    def _save_reminders(self):
        self.db.set_config("reminders_enabled", "true" if self._reminders_enabled.isChecked() else "false")
        self.db.set_config("reminder_morning_enabled", "true" if self._morning_cb.isChecked() else "false")
        self.db.set_config("reminder_evening_enabled", "true" if self._evening_cb.isChecked() else "false")
        self.db.set_config("reminder_night_enabled", "true" if self._night_cb.isChecked() else "false")
        self.db.set_config("reminder_morning", self._morning_time.time().toString("HH:mm"))
        self.db.set_config("reminder_evening", self._evening_time.time().toString("HH:mm"))
        self.db.set_config("reminder_night", self._night_time.time().toString("HH:mm"))
        QMessageBox.information(self, "Saved", "Reminder settings saved.")

    def _backup(self):
        try:
            path = self.db.backup()
            QMessageBox.information(self, "Backup", f"Database backed up to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Backup failed:\n{e}")

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", str(Path.home() / "planner_export.json"),
            "JSON Files (*.json)",
        )
        if path:
            try:
                self.db.export_json(path)
                QMessageBox.information(self, "Export", f"Data exported to:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Export failed:\n{e}")


def _parse_qtime(s: str) -> QTime:
    try:
        parts = s.split(":")
        return QTime(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return QTime(9, 0)
