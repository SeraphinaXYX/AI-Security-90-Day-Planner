"""AI Security 90-Day Planner — Application entry point."""
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
log = logging.getLogger(__name__)

# Ensure app package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.config import ensure_dirs, APP_NAME
from app.database import Database
from app.curriculum import get_curriculum
from app.scheduler import ReminderScheduler
from app.ui.styles import DARK_STYLESHEET
from app.ui.main_window import MainWindow


def main():
    ensure_dirs()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    font = QFont("Segoe UI", 10)
    app.setFont(font)
    app.setStyleSheet(DARK_STYLESHEET)

    # Initialize database and populate curriculum
    db = Database()
    curriculum = get_curriculum()
    db.get_start_date()  # ensures start_date is set
    db.populate_tasks(curriculum)
    log.info("Database initialized with %d curriculum days", len(curriculum))

    # Ask about startup on first launch
    first = db.get_config("startup_asked", "false")
    if first == "false":
        db.set_config("startup_asked", "true")
        # Startup registration is handled in Settings if user opts in

    # Start reminder scheduler
    scheduler = ReminderScheduler(db)
    if db.get_config("reminders_enabled", "true") == "true":
        scheduler.start()

    # Launch main window
    window = MainWindow(db, scheduler)
    window.show()

    ret = app.exec()
    scheduler.stop()
    db.close()
    sys.exit(ret)


if __name__ == "__main__":
    main()
