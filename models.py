"""Data classes: Expense, RecurringExpense, ExpenseBook, Budget."""
import datetime as dt
from dataclasses import dataclass

from utils import add_months

CATEGORIES = ("Food", "Transport", "Rent", "Bills", "Shopping",
              "Entertainment", "Health", "Education", "Other")


@dataclass
class Expense:
    """One expense entry. The dataclass writes __init__, __repr__ and __eq__ for us."""
    date: dt.date
    category: str
    amount: float
    note: str = ""

    def __post_init__(self):
        # Validation runs right after the automatic __init__
        if isinstance(self.date, str):
            self.date = dt.datetime.strptime(self.date, "%Y-%m-%d").date()
        if self.category not in CATEGORIES:
            raise ValueError(f"Category must be one of {', '.join(CATEGORIES)}")
        self.amount = float(self.amount)
        if self.amount <= 0:
            raise ValueError("Amount must be greater than 0")

    @property
    def month(self):
        return self.date.strftime("%Y-%m")

    @property
    def weekday(self):
        return self.date.strftime("%A")

    def to_dict(self):
        return {"date": self.date.isoformat(), "category": self.category,
                "amount": self.amount, "note": self.note}

    def __str__(self):
        return f"{self.date} | {self.category:<13} | Rs.{self.amount:>9.2f} | {self.note}"


@dataclass
class RecurringExpense(Expense):
    """Inheritance: an Expense that repeats every N months (rent, subscriptions)."""
    every_months: int = 1

    def generate(self, count):
        """Generator: yields one normal Expense per occurrence, one at a time."""
        for i in range(count):
            yield Expense(add_months(self.date, i * self.every_months),
                          self.category, self.amount, self.note)


class ExpenseBook:
    """A container of expenses. __len__ and __iter__ make it behave like a list."""

    def __init__(self, expenses=None):
        self._items = list(expenses or [])

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def add(self, expense):
        self._items.append(expense)

    def remove(self, expense):
        self._items.remove(expense)

    def months(self):
        return sorted({e.month for e in self._items})          # set comprehension

    def sorted_by_date(self):
        return sorted(self._items, key=lambda e: e.date)

    def filter(self, month=None, category=None):
        return [e for e in self._items                         # list comprehension
                if (month is None or e.month == month)
                and (category is None or e.category == category)]


class Budget:
    """Monthly limit per category."""

    def __init__(self, limits=None):
        self._limits = dict(limits or {})

    @property
    def limits(self):
        return dict(self._limits)          # a copy, so outside code can't change it by accident

    def set_limit(self, category, amount):
        if category not in CATEGORIES:
            raise ValueError("Unknown category")
        if amount <= 0:
            raise ValueError("Limit must be positive")
        self._limits[category] = float(amount)

    def status(self, category, spent):
        """Return (limit, label). Label is OK, WARNING (80%+), OVER or No limit."""
        limit = self._limits.get(category)
        if limit is None:
            return None, "No limit"
        used = spent / limit * 100
        return limit, ("OVER" if used > 100 else "WARNING" if used >= 80 else "OK")
