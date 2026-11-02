"""Background reminder scheduler using QTimer."""
import logging
from datetime import datetime, time as dt_time
from PySide6.QtCore import QTimer, QTime, QObject, Signal

from app.database import Database
from app.notifications import notify_morning, notify_evening, notify_night_check

log = logging.getLogger(__name__)


class ReminderScheduler(QObject):
    reminder_fired = Signal(str)  # signal with reminder type

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._timer = QTimer(self)
        self._timer.setInterval(60_000)  # check every 60 seconds
        self._timer.timeout.connect(self._check_reminders)
        self._fired_today: set[str] = set()
        self._last_date = datetime.now().date()

    def start(self):
        self._timer.start()
        log.info("Reminder scheduler started")

    def stop(self):
        self._timer.stop()
        log.info("Reminder scheduler stopped")

    def _reset_daily(self):
        today = datetime.now().date()
        if today != self._last_date:
            self._fired_today.clear()
            self._last_date = today

    def _check_reminders(self):
        self._reset_daily()

        enabled = self.db.get_config("reminders_enabled", "true") == "true"
        if not enabled:
            return

        now = datetime.now()
        current_time = now.time()
        day_num = self.db.get_today_day_number()
        if day_num < 1 or day_num > 90:
            return

        task = self.db.get_task(day_num)
        if not task:
            return
        topic = task.get("topic", "")

        # Morning reminder
        if self.db.get_config("reminder_morning_enabled", "true") == "true":
            morning_str = self.db.get_config("reminder_morning", "09:00")
            morning_time = _parse_time(morning_str)
            if morning_time and _in_window(current_time, morning_time) and "morning" not in self._fired_today:
                self._fired_today.add("morning")
                notify_morning(day_num, topic)
                self.reminder_fired.emit("morning")

        # Evening reminder
        if self.db.get_config("reminder_evening_enabled", "true") == "true":
            evening_str = self.db.get_config("reminder_evening", "19:00")
            evening_time = _parse_time(evening_str)
            if evening_time and _in_window(current_time, evening_time) and "evening" not in self._fired_today:
                self._fired_today.add("evening")
                notify_evening(day_num, topic)
                self.reminder_fired.emit("evening")

        # Night check
        if self.db.get_config("reminder_night_enabled", "true") == "true":
            night_str = self.db.get_config("reminder_night", "22:00")
            night_time = _parse_time(night_str)
            if night_time and _in_window(current_time, night_time) and "night" not in self._fired_today:
                self._fired_today.add("night")
                completed = task.get("status") == "completed"
                notify_night_check(day_num, completed)
                self.reminder_fired.emit("night")


def _parse_time(s: str) -> dt_time | None:
    try:
        parts = s.split(":")
        return dt_time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return None


def _in_window(current: dt_time, target: dt_time, window_minutes: int = 1) -> bool:
    """Check if current time is within window_minutes of target."""
    c = current.hour * 60 + current.minute
    t = target.hour * 60 + target.minute
    return 0 <= (c - t) < window_minutes
