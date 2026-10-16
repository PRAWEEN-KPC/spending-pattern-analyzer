"""File management: CSV, JSON and text files."""
import csv
import json
from contextlib import contextmanager
from pathlib import Path

from models import Expense

FIELDS = ["date", "category", "amount", "note"]


@contextmanager
def atomic_write(path):
    """Context manager: write to a temp file, then swap it in.
    If the program crashes mid-write, the old file stays safe."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with open(temp, "w", newline="", encoding="utf-8") as f:
        yield f
    temp.replace(path)


def load_expenses(path):
    path = Path(path)
    if not path.exists():
        return []
    expenses = []
    with open(path, newline="", encoding="utf-8") as f:
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                expenses.append(Expense(row["date"], row["category"], row["amount"], row.get("note", "")))
            except (ValueError, KeyError) as err:
                print(f"Skipped line {line_no}: {err}")
    return expenses


def save_expenses(path, expenses):
    with atomic_write(path) as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(e.to_dict() for e in expenses)


def load_budget(path):
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_budget(path, limits):
    with atomic_write(path) as f:
        json.dump(limits, f, indent=2)


def export_report(path, text):
    with atomic_write(path) as f:
        f.write(text)
