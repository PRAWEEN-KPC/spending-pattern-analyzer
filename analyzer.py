"""SpendingAnalyzer: mostly plain Python (collections, statistics, heapq).
pandas is used in ONE method (category_month_table); numpy in ONE method (forecast)."""
import datetime as dt
import heapq
import statistics
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from utils import WEEKDAYS, shift_month


class SpendingAnalyzer:
    def __init__(self, book):
        self.book = book

    def _items(self, month=None):
        """Generator expression: yields expenses lazily, optionally for one month."""
        return (e for e in self.book if month is None or e.month == month)

    # ---------- totals ----------
    def monthly_totals(self):
        totals = defaultdict(float)
        for e in self.book:
            totals[e.month] += e.amount
        return dict(sorted(totals.items()))

    def category_totals(self, month=None):
        totals = Counter()
        for e in self._items(month):
            totals[e.category] += e.amount
        return dict(totals.most_common())             # highest first

    def top_category(self, month=None):
        totals = self.category_totals(month)
        if not totals:
            return None, 0.0, 0.0
        name, amount = next(iter(totals.items()))
        return name, amount, amount / sum(totals.values()) * 100

    def month_change(self, month):
        """(this month, last month, % change or None)."""
        totals = self.monthly_totals()
        current, previous = totals.get(month, 0), totals.get(shift_month(month, -1), 0)
        pct = (current - previous) / previous * 100 if previous else None
        return current, previous, pct

    def daily_totals(self, month):
        days = defaultdict(float)
        for e in self._items(month):
            days[e.date.day] += e.amount
        return dict(sorted(days.items()))

    def weekday_totals(self, month=None):
        totals = dict.fromkeys(WEEKDAYS, 0.0)
        for e in self._items(month):
            totals[e.weekday] += e.amount
        return totals

    # ---------- comparisons and statistics ----------
    def compare_months(self, m1, m2):
        """List of (category, amount_m1, amount_m2, change, change_pct) sorted by change."""
        a, b = self.category_totals(m1), self.category_totals(m2)
        rows = []
        for cat in sorted(set(a) | set(b)):
            x, y = a.get(cat, 0), b.get(cat, 0)
            rows.append((cat, x, y, y - x, (y - x) / x * 100 if x else None))
        return sorted(rows, key=lambda r: r[3], reverse=True)

    def stats(self, month=None):
        amounts = [e.amount for e in self._items(month)]
        if not amounts:
            return {}
        return {"count": len(amounts), "total": sum(amounts),
                "mean": statistics.mean(amounts), "median": statistics.median(amounts),
                "stdev": statistics.stdev(amounts) if len(amounts) > 1 else 0.0,
                "max": max(amounts)}

    def biggest_expenses(self, month=None, n=5):
        return heapq.nlargest(n, self._items(month), key=lambda e: e.amount)

    def unusual_expenses(self, month=None, z=2.0):
        """Generator: yields expenses far above that category's normal amount."""
        by_cat = defaultdict(list)
        for e in self.book:
            by_cat[e.category].append(e.amount)
        limits = {}
        for cat, amounts in by_cat.items():
            if len(amounts) > 2:
                limits[cat] = statistics.mean(amounts) + z * statistics.stdev(amounts)
        for e in self._items(month):
            if e.category in limits and e.amount > limits[e.category]:
                yield e

    # ---------- forecast (numpy, light) ----------
    def past_totals(self):
        """Monthly totals up to the current month, so future-dated entries
        (e.g. recurring rent added in advance) don't distort the forecast."""
        totals = self.monthly_totals()
        this_month = dt.date.today().strftime("%Y-%m")
        past = {m: v for m, v in totals.items() if m <= this_month}
        return past if len(past) >= 2 else totals

    def forecast_next_month(self):
        totals = self.past_totals()
        if len(totals) < 2:
            return None
        values = list(totals.values())
        slope, intercept = np.polyfit(range(len(values)), values, 1)   # straight-line trend
        return {"next_month": shift_month(list(totals)[-1], 1),
                "avg_all": statistics.mean(values),
                "avg_last3": statistics.mean(values[-3:]),
                "trend": float(max(slope * len(values) + intercept, 0)),
                "std": statistics.pstdev(values),
                "slope": float(slope)}

    def forecast_by_category(self):
        """Average of each category over the last 3 months (plain Python)."""
        last3 = list(self.past_totals())[-3:]
        sums = defaultdict(float)
        for e in self.book:
            if e.month in last3:
                sums[e.category] += e.amount
        return dict(sorted(((c, s / len(last3)) for c, s in sums.items()),
                           key=lambda pair: pair[1], reverse=True))

    # ---------- budget ----------
    def budget_report(self, budget, month):
        spent = self.category_totals(month)
        rows = []
        for cat in sorted(set(spent) | set(budget.limits)):
            amount = spent.get(cat, 0.0)
            limit, label = budget.status(cat, amount)
            rows.append({"category": cat, "spent": amount, "limit": limit, "status": label})
        return rows

    # ---------- pandas (light): one pivot table for the heatmap ----------
    def category_month_table(self):
        df = pd.DataFrame([e.to_dict() for e in self.book])
        df["month"] = df["date"].str[:7]
        return df.pivot_table(index="category", columns="month",
                              values="amount", aggfunc="sum", fill_value=0)
