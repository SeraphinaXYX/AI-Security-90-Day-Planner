# AI Security 90-Day Learning Planner

A Windows desktop application for a structured 90-day AI Security learning journey, built with PySide6 and SQLite.

## Phases

| Phase | Days | Focus |
|-------|------|-------|
| 1 | 1–20 | Security & Engineering Foundations |
| 2 | 21–40 | AI Engineering & LLM Agents |
| 3 | 41–60 | AI Security & Red Teaming |
| 4 | 61–80 | Portfolio Research Project |
| 5 | 81–90 | Research & Internship Prep |

## Features

- **Dashboard** — overall progress, streak counter, weekly bar chart, phase breakdown
- **Today's Task** — daily topic with exercise, resources, deliverable, and notes
- **Calendar** — 90-day grid color-coded by completion status
- **Weekly Review** — reflection prompts and learnings per week
- **Notes** — searchable per-day notes with tags
- **Catch Up** — manage overdue tasks (complete, skip, or bulk-skip)
- **Settings** — 3 configurable reminders (morning/evening/night), backup, JSON export
- **Notifications** — Windows desktop notifications via plyer

## Setup

1. Install [Python 3.9+](https://www.python.org/downloads/) on Windows (check "Add Python to PATH")
2. Right-click `setup.ps1` → **Run with PowerShell**
3. The script creates a virtual environment, installs dependencies, and adds a desktop shortcut

Or manually:
```powershell
cd "C:\Users\hp\Desktop\AI-Security-90-Day-Planner"
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python main.py
```

## Data

- Database: `data/planner.db` (SQLite)
- Backups: `data/backups/`
- Config: `data/config.json`

## Project Structure

```
├── main.py                  # Entry point
├── setup.ps1                # One-click setup
├── launch.ps1               # Launcher
├── requirements.txt
├── app/
│   ├── config.py            # Paths and defaults
│   ├── curriculum.py        # 90-day learning content
│   ├── database.py          # SQLite operations
│   ├── notifications.py     # Windows notifications
│   ├── scheduler.py         # QTimer-based reminders
│   └── ui/
│       ├── styles.py        # Dark theme stylesheet
│       ├── main_window.py   # Sidebar + stack navigation
│       ├── dashboard.py     # Progress overview
│       ├── task_view.py     # Daily task details
│       ├── calendar_view.py # Month grid
│       ├── weekly_review.py # Reflection editor
│       ├── notes.py         # Note browser
│       ├── settings.py      # Config UI
│       └── catch_up.py      # Overdue task manager
└── tests/
    └── test_basics.py       # Curriculum + database tests
```
