"""Smart Spending Pattern Analyzer - menu-driven app."""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))   # always run from this folder

import charts
import file_handler as fh
import reports
import utils
from analyzer import SpendingAnalyzer
from models import CATEGORIES, Budget, Expense, ExpenseBook, RecurringExpense
from utils import handle_errors

DATA, BUDGET = "data/expenses.csv", "data/budget.json"

MENU = """
=== Smart Spending Pattern Analyzer ===
 1 Add expense      2 Add recurring    3 View          4 Search      5 Delete
 6 Summary          7 Compare months   8 Forecast      9 Budget     10 Unusual spends
 D Dashboard        E Export report    0 Exit"""


def show_list(items):
    if not items:
        print("Nothing to show.")
    for i, e in enumerate(items, start=1):
        print(f"{i:>3}. {e}")


class App:
    """Holds the data and one method per menu option."""

    def __init__(self):
        self.book = ExpenseBook(fh.load_expenses(DATA))
        self.budget = Budget(fh.load_budget(BUDGET))

    def save(self):
        fh.save_expenses(DATA, self.book)

    def has_data(self):
        if len(self.book) == 0:
            print("Add some expenses first.")
            return False
        return True

    def pick_month(self, allow_all=False):
        return utils.ask_month(self.book.months(), allow_all)

    # ---------- menu actions ----------
    @handle_errors
    def add(self):
        expense = Expense(utils.ask_date(), utils.ask_category(CATEGORIES),
                          utils.ask_float(), input("Note: ").strip())
        self.book.add(expense)
        self.save()
        print("Saved.")

    @handle_errors
    def add_recurring(self):
        rec = RecurringExpense(utils.ask_date("First date (YYYY-MM-DD, Enter = today): "),
                               utils.ask_category(CATEGORIES), utils.ask_float(),
                               input("Note: ").strip(),
                               every_months=utils.ask_int("Repeat every how many months (1 = monthly): ", 1, 12))
        count = utils.ask_int("How many times: ", 1, 60)
        added = 0
        for expense in rec.generate(count):     # generator gives one expense at a time
            self.book.add(expense)
            added += 1
        self.save()
        print(f"Added {added} entries.")

    @handle_errors
    def view(self):
        if self.has_data():
            show_list(sorted(self.book.filter(month=self.pick_month(True)), key=lambda e: e.date))

    @handle_errors
    def search(self):
        word = input("Search word (note or category): ").strip().lower()
        found = [e for e in self.book.sorted_by_date()
                 if word in e.note.lower() or word in e.category.lower()]
        show_list(found)
        print(f"{len(found)} match(es), total Rs.{sum(e.amount for e in found):,.2f}")

    @handle_errors
    def delete(self):
        if not self.has_data():
            return
        items = sorted(self.book.filter(month=self.pick_month(True)), key=lambda e: e.date)
        show_list(items)
        if items:
            choice = input("Number to delete (Enter = cancel): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(items):
                self.book.remove(items[int(choice) - 1])
                self.save()
                print("Deleted.")

    @handle_errors
    def summary(self):
        if not self.has_data():
            return
        an = SpendingAnalyzer(self.book)
        print("\nMonthly totals:")
        for month, total in an.monthly_totals().items():
            print(f"  {month}  Rs.{total:>10,.2f}")
        month = self.pick_month()
        cat, amt, share = an.top_category(month)
        s = an.stats(month)
        print(f"\nTop category in {month}: {cat} (Rs.{amt:,.2f}, {share:.1f}%)")
        print(f"Entries {s['count']} | average Rs.{s['mean']:,.2f} | median Rs.{s['median']:,.2f} "
              f"| std dev Rs.{s['stdev']:,.2f} | largest Rs.{s['max']:,.2f}")
        print("\nBy category:")
        for c, a in an.category_totals(month).items():
            print(f"  {c:<14}Rs.{a:>10,.2f}  {'#' * int(a / amt * 20)}")
        print("\nBiggest 5 expenses:")
        show_list(an.biggest_expenses(month, 5))

    @handle_errors
    def compare(self):
        if not self.has_data():
            return
        an = SpendingAnalyzer(self.book)
        m1, m2 = self.pick_month(), self.pick_month()
        print(f"\n{'Category':<14}{m1:>12}{m2:>12}{'Change':>12}{'%':>9}")
        for cat, a, b, change, pct in an.compare_months(m1, m2):
            pct_text = "-" if pct is None else f"{pct:+.0f}%"
            print(f"{cat:<14}{a:>12,.0f}{b:>12,.0f}{change:>+12,.0f}{pct_text:>9}")

    @handle_errors
    def forecast(self):
        if not self.has_data():
            return
        an = SpendingAnalyzer(self.book)
        f = an.forecast_next_month()
        if f is None:
            print("Need at least 2 months of data.")
            return
        print(f"\nEstimates for {f['next_month']}:")
        print(f"  Average of all months : Rs.{f['avg_all']:,.2f}")
        print(f"  Average of last 3     : Rs.{f['avg_last3']:,.2f}")
        print(f"  Trend-line estimate   : Rs.{f['trend']:,.2f}")
        print(f"  Typical variation     : +/- Rs.{f['std']:,.2f}")
        print("  Spending is", "rising" if f["slope"] > 0 else "falling",
              f"by about Rs.{abs(f['slope']):,.0f} per month")
        print("\nExpected by category (last-3 average):")
        for c, a in an.forecast_by_category().items():
            print(f"  {c:<14}Rs.{a:>10,.2f}")

    @handle_errors
    def budget_menu(self):
        choice = input("1 Set limit   2 Check a month: ").strip()
        if choice == "1":
            self.budget.set_limit(utils.ask_category(CATEGORIES), utils.ask_float("Monthly limit: "))
            fh.save_budget(BUDGET, self.budget.limits)
            print("Limit saved.")
        elif choice == "2" and self.has_data():
            an = SpendingAnalyzer(self.book)
            for r in an.budget_report(self.budget, self.pick_month()):
                limit = "-" if r["limit"] is None else f"{r['limit']:,.0f}"
                print(f"  {r['category']:<14}spent Rs.{r['spent']:>9,.0f}  limit {limit:>7}  {r['status']}")

    @handle_errors
    def unusual(self):
        if not self.has_data():
            return
        found = list(SpendingAnalyzer(self.book).unusual_expenses(self.pick_month(True)))
        print("Expenses far above their category's normal amount:")
        show_list(found)

    @handle_errors
    def dashboard(self):
        if self.has_data():
            charts.dashboard(SpendingAnalyzer(self.book), self.budget, self.pick_month())

    @handle_errors
    def export(self):
        if self.has_data():
            month = self.pick_month()
            text = reports.build_report(SpendingAnalyzer(self.book), self.budget, month)
            path = f"reports/report_{month}.txt"
            fh.export_report(path, text)
            print("Report exported:", path)

    # ---------- main loop ----------
    def run(self):
        actions = {"1": self.add, "2": self.add_recurring, "3": self.view, "4": self.search,
                   "5": self.delete, "6": self.summary, "7": self.compare, "8": self.forecast,
                   "9": self.budget_menu, "10": self.unusual, "D": self.dashboard, "E": self.export}
        while True:
            print(MENU)
            choice = input("Choose: ").strip().upper()
            if choice == "0":
                print("Goodbye!")
                break
            action = actions.get(choice)
            if action:
                action()
            else:
                print("Invalid choice.")


if __name__ == "__main__":
    utils.setup_logging()
    App().run()
