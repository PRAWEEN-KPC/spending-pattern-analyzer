"""matplotlib dashboard built from the analyzer's results."""
import itertools
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

from utils import timed


def _finish(fig, path, show):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    print(f"Chart saved: {path}")
    if show:
        plt.show()
    plt.close(fig)


@timed
def dashboard(an, budget, month, path="charts/dashboard.png", show=True):
    """One window: 3 KPI cards + 6 charts for the chosen month."""
    total, prev, pct = an.month_change(month)
    cat, amt, share = an.top_category(month)
    fc = an.forecast_next_month()

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(f"Spending Dashboard - {month}", fontsize=18, fontweight="bold")
    gs = GridSpec(3, 3, figure=fig, height_ratios=[0.5, 1, 1], hspace=0.5, wspace=0.3)

    # Row 0: KPI cards
    cards = [("Total spent", f"Rs.{total:,.0f}",
              "no previous month" if pct is None else f"{pct:+.1f}% vs last month"),
             ("Top category", str(cat), f"Rs.{amt:,.0f} ({share:.0f}% of spend)"),
             ("Next month estimate", f"Rs.{fc['trend']:,.0f}" if fc else "n/a",
              f"average Rs.{fc['avg_all']:,.0f}" if fc else "need 2+ months")]
    for i, (title, big, small) in enumerate(cards):
        ax = fig.add_subplot(gs[0, i])
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, color="#EEF3F9", transform=ax.transAxes))
        ax.text(0.5, 0.78, title, ha="center", fontsize=11, color="#555")
        ax.text(0.5, 0.42, big, ha="center", fontsize=20, fontweight="bold")
        ax.text(0.5, 0.12, small, ha="center", fontsize=10, color="#555")

    # Row 1: category bars | monthly trend | daily + cumulative
    ax = fig.add_subplot(gs[1, 0])
    cats = dict(reversed(list(an.category_totals(month).items())))
    ax.barh(list(cats), list(cats.values()), color="#4C78A8")
    ax.set_title("By category")

    ax = fig.add_subplot(gs[1, 1])
    monthly = an.past_totals()
    ax.plot(list(monthly), list(monthly.values()), marker="o", color="#E45756", label="Actual")
    if fc:
        ax.plot([list(monthly)[-1], "next"], [list(monthly.values())[-1], fc["trend"]],
                "--o", color="gray", label="Forecast")
    ax.set_title("Monthly trend")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=40, ha="right")

    ax = fig.add_subplot(gs[1, 2])
    daily = an.daily_totals(month)
    ax.bar(list(daily), list(daily.values()), color="#9ECAE9")
    ax2 = ax.twinx()
    ax2.plot(list(daily), list(itertools.accumulate(daily.values())), color="#F58518")
    ax.set_title("Daily and cumulative")
    ax.set_xlabel("Day of month")

    # Row 2: weekday | budget vs spent | heatmap
    ax = fig.add_subplot(gs[2, 0])
    week = an.weekday_totals(month)
    ax.bar([d[:3] for d in week], list(week.values()), color="#72B7B2")
    ax.set_title("By weekday")

    ax = fig.add_subplot(gs[2, 1])
    rows = [r for r in an.budget_report(budget, month) if r["limit"]]
    if rows:
        x = np.arange(len(rows))
        ax.bar(x - 0.2, [r["limit"] for r in rows], 0.4, color="#BBBBBB", label="Limit")
        ax.bar(x + 0.2, [r["spent"] for r in rows], 0.4, label="Spent",
               color=["#E45756" if r["status"] == "OVER" else "#54A24B" for r in rows])
        ax.set_xticks(x)
        ax.set_xticklabels([r["category"] for r in rows], rotation=40, ha="right")
        ax.legend()
    else:
        ax.axis("off")
        ax.text(0.5, 0.5, "No budget limits set.\nUse menu option 9.",
                ha="center", va="center", fontsize=11, color="#777")
    ax.set_title("Budget vs spent")

    ax = fig.add_subplot(gs[2, 2])
    table = an.category_month_table()
    table = table[[m for m in table.columns if m in monthly]]   # skip future months
    im = ax.imshow(table.values, aspect="auto", cmap="Blues")
    ax.set_yticks(range(len(table.index)))
    ax.set_yticklabels(table.index, fontsize=8)
    ax.set_xticks(range(len(table.columns)))
    ax.set_xticklabels(table.columns, rotation=40, ha="right", fontsize=8)
    ax.set_title("Category x month")
    fig.colorbar(im, ax=ax, fraction=0.046)

    _finish(fig, path, show)
