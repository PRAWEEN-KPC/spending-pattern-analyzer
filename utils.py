"""Helpers: date maths, validated input, decorators, logging."""
import calendar
import datetime as dt
import functools
import logging
import time

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def setup_logging():
    logging.basicConfig(filename="app.log", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")


# ---------- decorators ----------
def handle_errors(func):
    """Decorator: show friendly messages and log unexpected crashes."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, KeyError) as err:
            print("Error:", err)
        except Exception:
            logging.exception("Unexpected error in %s", func.__name__)
            print("Something went wrong. Details were saved in app.log")
    return wrapper


def timed(func):
    """Decorator: print how long a function took."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"({func.__name__} took {time.perf_counter() - start:.2f}s)")
        return result
    return wrapper


# ---------- date maths ----------
def add_months(d, n):
    """Return date d moved by n months (n can be negative); day is clipped to month end."""
    year_shift, month_index = divmod(d.month - 1 + n, 12)
    year, month = d.year + year_shift, month_index + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day)


def shift_month(month_text, n):
    """'2026-09' + 1 -> '2026-10'."""
    y, m = map(int, month_text.split("-"))
    return add_months(dt.date(y, m, 1), n).strftime("%Y-%m")


# ---------- validated input ----------
def ask_date(prompt="Date (YYYY-MM-DD, Enter = today): "):
    while True:
        text = input(prompt).strip()
        if not text:
            return dt.date.today()
        try:
            return dt.datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            print("Invalid date. Example: 2026-09-30")


def ask_float(prompt="Amount: "):
    while True:
        try:
            value = float(input(prompt))
            if value > 0:
                return value
            print("Must be greater than 0.")
        except ValueError:
            print("Enter a number.")


def ask_int(prompt, low, high):
    while True:
        text = input(prompt).strip()
        if text.isdigit() and low <= int(text) <= high:
            return int(text)
        print(f"Enter a whole number from {low} to {high}.")


def ask_category(categories):
    for i, name in enumerate(categories, start=1):
        print(f"  {i}. {name}")
    return categories[ask_int("Category number: ", 1, len(categories)) - 1]


def ask_month(months, allow_all=False):
    """Ask for a month that exists in the data. Enter returns None when allow_all=True."""
    print("Available:", ", ".join(months))
    while True:
        text = input("Month (YYYY-MM)" + (", Enter = all" if allow_all else "") + ": ").strip()
        if allow_all and not text:
            return None
        if text in months:
            return text
        print("Month not found in your data.")
