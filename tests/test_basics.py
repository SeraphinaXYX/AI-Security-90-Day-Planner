"""Basic tests for the planner application."""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Database
from app.curriculum import get_curriculum
from app.config import DEFAULT_CONFIG


def test_curriculum_completeness():
    """All 90 days present with required fields."""
    curriculum = get_curriculum()
    assert len(curriculum) == 90, f"Expected 90 days, got {len(curriculum)}"

    required_fields = [
        "day", "phase", "phase_name", "topic", "concepts",
        "exercise", "resources", "estimated_minutes", "deliverable",
    ]

    days_seen = set()
    for item in curriculum:
        for field in required_fields:
            assert field in item, f"Day {item.get('day', '?')} missing field: {field}"

        assert isinstance(item["concepts"], list) and len(item["concepts"]) >= 2, \
            f"Day {item['day']}: concepts must be a list with >= 2 items"
        assert isinstance(item["resources"], list) and len(item["resources"]) >= 1, \
            f"Day {item['day']}: resources must be a non-empty list"
        assert 30 <= item["estimated_minutes"] <= 180, \
            f"Day {item['day']}: estimated_minutes out of range"
        assert len(item["exercise"]) >= 50, \
            f"Day {item['day']}: exercise too short ({len(item['exercise'])} chars)"
        assert len(item["topic"]) >= 5, \
            f"Day {item['day']}: topic too short"

        for res in item["resources"]:
            assert "title" in res and "url" in res, \
                f"Day {item['day']}: resource missing title/url"

        days_seen.add(item["day"])

    assert days_seen == set(range(1, 91)), "Not all days 1-90 are present"
    print("PASS: curriculum_completeness")


def test_curriculum_uniqueness():
    """All topics are unique."""
    curriculum = get_curriculum()
    topics = [item["topic"] for item in curriculum]
    dupes = [t for t in topics if topics.count(t) > 1]
    assert len(set(dupes)) == 0, f"Duplicate topics: {set(dupes)}"
    print("PASS: curriculum_uniqueness")


def test_curriculum_phases():
    """Phase assignments are correct."""
    curriculum = get_curriculum()
    for item in curriculum:
        d = item["day"]
        expected_phase = (
            1 if d <= 20 else
            2 if d <= 40 else
            3 if d <= 60 else
            4 if d <= 80 else 5
        )
        assert item["phase"] == expected_phase, \
            f"Day {d}: expected phase {expected_phase}, got {item['phase']}"
    print("PASS: curriculum_phases")


def test_database_operations():
    """Database CRUD works."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = Database(db_path)
        curriculum = get_curriculum()
        db.populate_tasks(curriculum)

        # Get task
        task = db.get_task(1)
        assert task["day"] == 1
        assert task["phase"] == 1

        # Update status
        db.update_task_status(1, "completed")
        task = db.get_task(1)
        assert task["status"] == "completed"
        assert task["completed_at"] is not None

        # Progress stats
        stats = db.get_progress_stats()
        assert stats["completed"] == 1
        assert stats["total"] == 90

        # Notes
        db.save_note(1, "Learned about HTTP requests", "python,http")
        note = db.get_note(1)
        assert note["text"] == "Learned about HTTP requests"
        assert note["tags"] == "python,http"

        # Search notes
        results = db.search_notes("HTTP")
        assert len(results) == 1

        # Weekly review
        db.save_weekly_review(1, "Good week", "Learned Python basics")
        review = db.get_weekly_review(1)
        assert review["reflection"] == "Good week"

        # Config
        db.set_config("test_key", "test_value")
        assert db.get_config("test_key") == "test_value"
        assert db.get_config("missing", "default") == "default"

        # Export
        export_path = db_path + ".json"
        db.export_json(export_path)
        with open(export_path) as f:
            data = json.load(f)
        assert len(data["tasks"]) == 90
        os.unlink(export_path)

        db.close()
        print("PASS: database_operations")
    finally:
        os.unlink(db_path)


def test_database_streak():
    """Streak calculation works."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = Database(db_path)
        curriculum = get_curriculum()
        db.populate_tasks(curriculum)

        today = db.get_today_day_number()
        if 1 <= today <= 90:
            db.update_task_status(today, "completed")
            assert db.get_streak() >= 1

        db.close()
        print("PASS: database_streak")
    finally:
        os.unlink(db_path)


def test_database_populate_idempotent():
    """Populating tasks twice doesn't duplicate."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = Database(db_path)
        curriculum = get_curriculum()
        db.populate_tasks(curriculum)
        db.populate_tasks(curriculum)  # second call
        tasks = db.get_all_tasks()
        assert len(tasks) == 90
        db.close()
        print("PASS: database_populate_idempotent")
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    test_curriculum_completeness()
    test_curriculum_uniqueness()
    test_curriculum_phases()
    test_database_operations()
    test_database_streak()
    test_database_populate_idempotent()
    print("\nAll tests passed!")
