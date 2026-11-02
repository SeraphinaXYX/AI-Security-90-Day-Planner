"""Windows desktop notification system using plyer."""
import sys
import logging
from datetime import datetime

log = logging.getLogger(__name__)

_PLYER_AVAILABLE = False
try:
    from plyer import notification as plyer_notify
    _PLYER_AVAILABLE = True
except ImportError:
    pass


def notify(title: str, message: str, timeout: int = 10):
    """Send a Windows desktop notification."""
    if not _PLYER_AVAILABLE:
        log.warning("plyer not available, notification skipped: %s", title)
        return False

    try:
        plyer_notify.notify(
            title=title,
            message=message,
            app_name="AI Security Planner",
            timeout=timeout,
        )
        return True
    except Exception as e:
        log.warning("Notification failed: %s", e)
        return False


def notify_morning(day_num: int, topic: str):
    notify(
        f"Day {day_num} — Good Morning!",
        f"Today's topic: {topic}\nOpen the planner to see your tasks.",
    )


def notify_evening(day_num: int, topic: str):
    notify(
        f"Day {day_num} — Time to Study",
        f"Topic: {topic}\nStart working on today's exercise.",
    )


def notify_night_check(day_num: int, completed: bool):
    if completed:
        notify(
            f"Day {day_num} — Great Work!",
            "You completed today's task. Keep the streak going!",
        )
    else:
        notify(
            f"Day {day_num} — Task Incomplete",
            "Open the planner to mark your progress or postpone.",
        )


def notify_motivation(day_num: int):
    messages = [
        "Every expert was once a beginner. Keep going!",
        "Consistency beats intensity. Show up today.",
        "You're building skills that matter. Stay focused.",
        "Small daily progress adds up to big results.",
        "The best time to start was yesterday. The next best time is now.",
    ]
    msg = messages[day_num % len(messages)]
    notify("AI Security Journey", msg, timeout=8)
