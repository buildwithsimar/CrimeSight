"""Matplotlib chart builders (dark theme) and summary stats. Works on lists of dict rows."""
from collections import Counter

from matplotlib.figure import Figure

BG = "#1e2230"
FG = "#e6e8ee"
PALETTE = ["#4cc9f0", "#f72585", "#b5179e", "#7209b7", "#4361ee", "#f8961e",
           "#90be6d", "#f9c74f", "#43aa8b", "#ef476f", "#8d99ae", "#06d6a0"]


def summary(rows):
    if not rows:
        return dict(total=0, open=0, solved=0.0, top_crime="-", top_area="-")
    closed = sum(r["status"] == "Closed" for r in rows)
    return dict(
        total=len(rows),
        open=len(rows) - closed,
        solved=round(closed / len(rows) * 100, 1),
        top_crime=Counter(r["crime_type"] for r in rows).most_common(1)[0][0],
        top_area=Counter(r["area"] for r in rows).most_common(1)[0][0],
    )


def insights(rows, this_year, last_year):
    """Text insights for the Analytics tab."""
    if not rows:
        return "No data."
    hours = Counter(int(r["time"][:2]) for r in rows)
    peak = hours.most_common(1)[0][0]
    night = sum(v for h, v in hours.items() if h >= 20 or h < 5) / len(rows) * 100
    high = [r for r in rows if r["severity"] == "High"]
    worst = Counter(r["area"] for r in high).most_common(1)[0][0] if high else "-"
    a = sum(r["date"].startswith(str(this_year)) for r in rows)
    b = sum(r["date"].startswith(str(last_year)) for r in rows)
    chg = f"{(a - b) / b * 100:+.0f}%" if b else "n/a"
    return (f"INSIGHTS  >  Peak hour: {peak:02d}:00  |  Night-time crimes (8PM-5AM): {night:.0f}%  |  "
            f"High-severity cases: {len(high)} (worst area: {worst})  |  "
            f"{this_year} vs {last_year}: {a} vs {b} ({chg})")


def _style(ax, title):
    ax.set_facecolor(BG)
    ax.set_title(title, color=FG, fontsize=11, fontweight="bold", pad=10)
    ax.tick_params(colors=FG, labelsize=8)
    for s in ax.spines.values():
        s.set_color("#3a4056")


def _empty(ax, title):
    _style(ax, title)
    ax.text(0.5, 0.5, "No data", color=FG, ha="center", va="center", transform=ax.transAxes)


def pie_types(rows, ax):
    if not rows:
        return _empty(ax, "Crime Types")
    c = Counter(r["crime_type"] for r in rows).most_common()
    top = c[:7]
    if len(c) > 7:
        top.append(("Others", sum(v for _, v in c[7:])))
    ax.pie([v for _, v in top], labels=[k for k, _ in top], autopct="%1.0f%%",
           startangle=90, colors=PALETTE, textprops={"color": FG, "fontsize": 7},
           wedgeprops={"edgecolor": BG}, pctdistance=0.8)
    ax.set_title("Crime Types", color=FG, fontsize=11, fontweight="bold")


def bar_areas(rows, ax):
    if not rows:
        return _empty(ax, "Crimes per Area")
    c = sorted(Counter(r["area"] for r in rows).items(), key=lambda kv: kv[1])
    ax.barh([k for k, _ in c], [v for _, v in c], color="#4cc9f0")
    _style(ax, "Crimes per Area")
    for i, (_, v) in enumerate(c):
        ax.text(v + 0.5, i, str(v), color=FG, va="center", fontsize=7)


def line_months(rows, ax):
    if not rows:
        return _empty(ax, "Monthly Trend")
    c = sorted(Counter(r["date"][:7] for r in rows).items())[-18:]
    x, y = [k for k, _ in c], [v for _, v in c]
    ax.plot(x, y, color="#f72585", marker="o", linewidth=2)
    ax.fill_between(x, y, color="#f72585", alpha=0.15)
    _style(ax, "Monthly Trend (last 18 months)")
    ax.tick_params(axis="x", rotation=60)
    ax.grid(color="#2c3246", linewidth=0.6)


def bar_hours(rows, ax):
    if not rows:
        return _empty(ax, "Crimes by Hour of Day")
    c = Counter(int(r["time"][:2]) for r in rows)
    ax.bar(range(24), [c.get(h, 0) for h in range(24)], color="#f8961e")
    _style(ax, "Crimes by Hour of Day")
    ax.set_xticks(range(0, 24, 3))


def bar_status(rows, ax):
    if not rows:
        return _empty(ax, "Case Status")
    order = ["Open", "Under Investigation", "Closed"]
    c = Counter(r["status"] for r in rows)
    cols = ["#ef476f", "#f9c74f", "#06d6a0"]
    bars = ax.bar(order, [c.get(s, 0) for s in order], color=cols)
    _style(ax, "Case Status")
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), int(b.get_height()),
                color=FG, ha="center", va="bottom", fontsize=8)


def heat_area_type(rows, ax):
    if not rows:
        return _empty(ax, "Hotspot Heatmap")
    areas = sorted({r["area"] for r in rows})
    types = sorted({r["crime_type"] for r in rows})
    c = Counter((r["area"], r["crime_type"]) for r in rows)
    grid = [[c.get((a, t), 0) for t in types] for a in areas]
    ax.imshow(grid, cmap="magma", aspect="auto")
    ax.set_xticks(range(len(types)))
    ax.set_xticklabels(types, rotation=60, ha="right")
    ax.set_yticks(range(len(areas)))
    ax.set_yticklabels(areas)
    _style(ax, "Hotspot Heatmap: Area vs Crime Type")
    ax.tick_params(labelsize=7)


def build_figure(rows, kind, size=(5, 3)):
    fig = Figure(figsize=size, dpi=100, facecolor=BG)
    kind(rows, fig.add_subplot(111))
    fig.tight_layout()
    return fig
