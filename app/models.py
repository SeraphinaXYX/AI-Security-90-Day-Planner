"""Data models used across the application."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    day: int
    phase: int
    phase_name: str
    title: str
    description: str
    difficulty: str
    duration: str
    resources: list = field(default_factory=list)
    status: str = "pending"


@dataclass
class Note:
    day: int
    text: str
    tags: str = ""


@dataclass
class WeeklyReviewData:
    week: int
    reflection: str
    learnings: str
