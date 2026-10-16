"""Run all tests:  python -m unittest -v"""
import datetime as dt
import unittest

from analyzer import SpendingAnalyzer
from models import Budget, Expense, ExpenseBook, RecurringExpense
from utils import add_months, shift_month


class TestExpense(unittest.TestCase):
    def test_valid_expense(self):
        e = Expense("2026-09-05", "Food", "120.5", "lunch")
        self.assertEqual(e.month, "2026-09")
        self.assertEqual(e.amount, 120.5)

    def test_bad_amount(self):
        with self.assertRaises(ValueError):
            Expense("2026-09-05", "Food", -5)

    def test_bad_category(self):
        with self.assertRaises(ValueError):
            Expense("2026-09-05", "Pizza", 50)


class TestDates(unittest.TestCase):
    def test_add_months_clips_day(self):
        self.assertEqual(add_months(dt.date(2026, 1, 31), 1), dt.date(2026, 2, 28))

    def test_shift_month(self):
        self.assertEqual(shift_month("2026-12", 1), "2027-01")
        self.assertEqual(shift_month("2026-01", -1), "2025-12")


class TestRecurring(unittest.TestCase):
    def test_generate(self):
        rec = RecurringExpense("2026-01-05", "Rent", 6500, "rent", every_months=1)
        dates = [e.date for e in rec.generate(3)]
        self.assertEqual(dates, [dt.date(2026, 1, 5), dt.date(2026, 2, 5), dt.date(2026, 3, 5)])


class TestAnalyzer(unittest.TestCase):
    def setUp(self):
        book = ExpenseBook([Expense("2026-08-01", "Food", 100), Expense("2026-08-02", "Rent", 500),
                            Expense("2026-09-01", "Food", 300), Expense("2026-09-03", "Bills", 100)])
        self.an = SpendingAnalyzer(book)

    def test_monthly_totals(self):
        self.assertEqual(self.an.monthly_totals(), {"2026-08": 600.0, "2026-09": 400.0})

    def test_top_category(self):
        self.assertEqual(self.an.top_category("2026-09")[0], "Food")

    def test_month_change(self):
        self.assertAlmostEqual(self.an.month_change("2026-09")[2], -33.333, places=2)


class TestBudget(unittest.TestCase):
    def test_status(self):
        b = Budget({"Food": 1000})
        self.assertEqual(b.status("Food", 500)[1], "OK")
        self.assertEqual(b.status("Food", 850)[1], "WARNING")
        self.assertEqual(b.status("Food", 1200)[1], "OVER")
        self.assertEqual(b.status("Rent", 10)[1], "No limit")


if __name__ == "__main__":
    unittest.main()
