"""Builds the text report using f-strings."""


def build_report(an, budget, month):
    total, prev, pct = an.month_change(month)
    cat, amt, share = an.top_category(month)
    s = an.stats(month)
    lines = [f"SPENDING REPORT - {month}", "=" * 44,
             f"Total spent     : Rs.{total:,.2f}",
             f"Previous month  : Rs.{prev:,.2f}" + ("" if pct is None else f"  ({pct:+.1f}%)"),
             f"Top category    : {cat} ({share:.1f}%)",
             f"Entries         : {s['count']}  (average Rs.{s['mean']:,.2f}, median Rs.{s['median']:,.2f})",
             "", "By category:"]
    lines += [f"  {c:<14}Rs.{a:>10,.2f}" for c, a in an.category_totals(month).items()]
    lines += ["", "Biggest expenses:"]
    lines += [f"  {e}" for e in an.biggest_expenses(month, 5)]
    lines += ["", "Budget status:"]
    rows = an.budget_report(budget, month)
    lines += [f"  {r['category']:<14}Rs.{r['spent']:>10,.2f}  limit "
              f"{'-' if r['limit'] is None else format(r['limit'], ',.0f'):>8}  {r['status']}"
              for r in rows]
    return "\n".join(lines) + "\n"
