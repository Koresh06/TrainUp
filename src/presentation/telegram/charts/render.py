"""PNG-графики статистики (matplotlib, без GUI-бэкенда).

Стиль общий для всех графиков: светлая карточка, приглушённая сетка, тонкие
столбики со скруглённым верхом, легенда сверху, итог в подзаголовке. Цвета
серий закреплены за смыслом (проведено — синий, запланировано — голубой,
отменено — красный и т.д.) и не зависят от того, сколько серий на графике.
"""

import io
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from matplotlib.ticker import FuncFormatter, MaxNLocator  # noqa: E402

SURFACE = "#fcfcfb"
GRID = "#e6e5e1"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#8a8984"

BLUE = "#2a78d6"
BLUE_LIGHT = "#9ec5f4"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
VIOLET = "#6250d6"
RED = "#e34948"

SEQUENTIAL = ["#f3f7fd", "#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#104281"]

MONTHS_SHORT = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
WEEKDAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

WIDTH, HEIGHT, DPI = 8.0, 4.6, 160


@dataclass(frozen=True)
class Series:
    label: str
    values: Sequence[float | None]
    color: str


def _figure(title: str, subtitle: str) -> tuple[Figure, Axes]:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.edgecolor": GRID,
            "axes.labelcolor": TEXT_SECONDARY,
            "xtick.color": TEXT_SECONDARY,
            "ytick.color": TEXT_SECONDARY,
        }
    )
    fig = plt.figure(figsize=(WIDTH, HEIGHT), dpi=DPI, facecolor=SURFACE)
    ax = fig.add_axes((0.075, 0.13, 0.9, 0.62), facecolor=SURFACE)
    fig.text(0.04, 0.925, title, fontsize=15, fontweight="bold", color=TEXT_PRIMARY)
    fig.text(0.04, 0.865, subtitle, fontsize=10, color=TEXT_SECONDARY)

    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="both", length=0, pad=6)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    return fig, ax


def _to_png(fig: Figure) -> bytes:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", facecolor=SURFACE)
    plt.close(fig)
    return buffer.getvalue()


def _bucket_labels(buckets: Sequence[date], by_month: bool) -> list[str]:
    if by_month:
        return [f"{MONTHS_SHORT[d.month - 1]}\n{d:%y}" for d in buckets]
    return [f"{d:%d.%m}" if len(buckets) > 7 else f"{WEEKDAYS_SHORT[d.weekday()]}\n{d:%d.%m}" for d in buckets]


def _x_ticks(ax: Axes, buckets: Sequence[date], by_month: bool) -> None:
    labels = _bucket_labels(buckets, by_month)
    # не больше ~12 подписей, иначе на телефоне они слипаются
    step = max(1, -(-len(buckets) // 12))
    ticks = list(range(0, len(buckets), step))
    ax.set_xticks(ticks, [labels[i] for i in ticks])
    ax.set_xlim(-0.6, len(buckets) - 0.4)


def _y_axis(ax: Axes, top: float, money: str | None) -> None:
    ax.set_ylim(0, max(top * 1.18, 1))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5, integer=money is None, min_n_ticks=2))

    def compact(value: float, _pos: int) -> str:
        if value >= 1000:
            text = f"{value / 1000:.1f}".rstrip("0").rstrip(".") + "K"
        else:
            text = f"{value:.0f}"
        return f"{text} {money}" if money and value else text

    ax.yaxis.set_major_formatter(FuncFormatter(compact))


def _rounded_bar(ax: Axes, x: float, bottom: float, height: float, width: float, color: str, round_top: bool) -> None:
    """Столбик со скруглённым верхом (~4px) и прямым основанием. Радиус задан
    в пикселях, поэтому переводим его в единицы осей X и Y отдельно
    (mutation_aspect), а низ «досыпаем» прямоугольником."""
    if height <= 0:
        return
    if not round_top:
        ax.bar(x, height, width=width, bottom=bottom, color=color, linewidth=0)
        return
    bbox = ax.get_window_extent()
    px_per_x = bbox.width / (ax.get_xlim()[1] - ax.get_xlim()[0])
    px_per_y = bbox.height / (ax.get_ylim()[1] - ax.get_ylim()[0])
    radius_px = 4 * DPI / 100
    radius_x = min(radius_px / px_per_x, width / 2)
    radius_y = min(radius_px / px_per_y, height)
    ax.add_patch(
        FancyBboxPatch(
            (x - width / 2, bottom), width, height,
            boxstyle=f"round,pad=0,rounding_size={radius_x}",
            mutation_aspect=radius_y / radius_x,
            facecolor=color, linewidth=0,
        )
    )
    ax.bar(x, radius_y, width=width, bottom=bottom, color=color, linewidth=0)


def _legend(fig: Figure, series: Sequence[Series]) -> None:
    if len(series) < 2:
        return
    x = 0.04
    for item in series:
        fig.patches.append(
            FancyBboxPatch(
                (x, 0.795), 0.014, 0.024, boxstyle="round,pad=0,rounding_size=0.004",
                transform=fig.transFigure, facecolor=item.color, linewidth=0,
            )
        )
        label = fig.text(x + 0.022, 0.799, item.label, fontsize=9.5, color=TEXT_SECONDARY)
        fig.canvas.draw()
        width = label.get_window_extent().width / fig.bbox.width
        x += 0.022 + width + 0.035


def _highlight_today(ax: Axes, buckets: Sequence[date], today: date | None, by_month: bool) -> None:
    if today is None:
        return
    key = today.replace(day=1) if by_month else today
    if key in buckets and len(buckets) > 1:
        i = list(buckets).index(key)
        ax.axvspan(i - 0.5, i + 0.5, color="#f1f0ec", zorder=0, linewidth=0)


def stacked_bars(
    *,
    title: str,
    subtitle: str,
    buckets: Sequence[date],
    by_month: bool,
    series: Sequence[Series],
    today: date | None = None,
    money: str | None = None,
) -> bytes:
    """Столбики по дням/месяцам; несколько серий складываются в стопку
    с зазором 2px между сегментами."""
    fig, ax = _figure(title, subtitle)
    _x_ticks(ax, buckets, by_month)
    totals = [sum(float(s.values[i]) for s in series) for i in range(len(buckets))]
    _y_axis(ax, max(totals, default=0), money)
    _highlight_today(ax, buckets, today, by_month)
    fig.canvas.draw()

    width = 0.62 if len(buckets) <= 16 else 0.72
    gap = (ax.get_ylim()[1] / (ax.get_window_extent().height or 1)) * 2
    for i in range(len(buckets)):
        bottom = 0.0
        filled = [s for s in series if float(s.values[i]) > 0]
        for n, item in enumerate(filled):
            height = float(item.values[i])
            is_top = n == len(filled) - 1
            visible = height - (0 if is_top else gap)
            _rounded_bar(ax, i, bottom, max(visible, height * 0.5), width, item.color, round_top=is_top)
            bottom += height

    # подпись только у максимума — остальное читается по оси
    if totals and max(totals) > 0:
        peak = max(range(len(totals)), key=lambda i: totals[i])
        value = totals[peak]
        text = f"{value:,.0f}".replace(",", " ")
        ax.annotate(
            f"{text} {money}" if money else text,
            (peak, value), xytext=(0, 5), textcoords="offset points",
            ha="center", fontsize=9, color=TEXT_PRIMARY, fontweight="bold",
        )
    _legend(fig, series)
    return _to_png(fig)


def line_with_bars(
    *,
    title: str,
    subtitle: str,
    buckets: Sequence[date],
    by_month: bool,
    line: Series,
    bars: Series,
    today: date | None = None,
) -> bytes:
    """Линия (с лёгкой заливкой) + столбики одной размерности на одной оси —
    например, активные пользователи и заблокировавшие бота."""
    fig, ax = _figure(title, subtitle)
    _x_ticks(ax, buckets, by_month)
    top = max([*(float(v) for v in line.values if v is not None), *map(float, bars.values), 0])
    _y_axis(ax, top, None)
    _highlight_today(ax, buckets, today, by_month)
    fig.canvas.draw()

    xs = list(range(len(buckets)))
    for i, value in enumerate(bars.values):
        _rounded_bar(ax, i, 0, float(value), 0.38, bars.color, round_top=True)

    # None — будущие дни: линия обрывается на сегодня, а не падает в ноль
    known = [(x, float(v)) for x, v in zip(xs, line.values) if v is not None]
    if known:
        lx, ly = zip(*known)
        ax.fill_between(lx, ly, color=line.color, alpha=0.10, linewidth=0)
        ax.plot(lx, ly, color=line.color, linewidth=2, solid_capstyle="round", solid_joinstyle="round")
        ax.scatter([lx[-1]], [ly[-1]], s=42, color=line.color, edgecolors=SURFACE, linewidths=2, zorder=5)
        ax.annotate(
            f"{ly[-1]:.0f}", (lx[-1], ly[-1]), xytext=(0, 8), textcoords="offset points",
            ha="center", fontsize=9, color=TEXT_PRIMARY, fontweight="bold",
        )
    _legend(fig, [line, bars])
    return _to_png(fig)


def weekly_heatmap(*, title: str, subtitle: str, load: Sequence[Sequence[int]]) -> bytes:
    """Загрузка по дням недели и часам: чем темнее клетка, тем больше занятий."""
    fig = plt.figure(figsize=(WIDTH, HEIGHT), dpi=DPI, facecolor=SURFACE)
    fig.text(0.04, 0.925, title, fontsize=15, fontweight="bold", color=TEXT_PRIMARY)
    fig.text(0.04, 0.865, subtitle, fontsize=10, color=TEXT_SECONDARY)
    ax = fig.add_axes((0.075, 0.1, 0.9, 0.7), facecolor=SURFACE)

    busy_hours = [h for h in range(24) if any(load[d][h] for d in range(7))]
    first = min(busy_hours, default=8)
    last = max(busy_hours, default=21)
    first, last = min(first, 8), max(last, 20)
    hours = list(range(first, last + 1))
    peak = max((load[d][h] for d in range(7) for h in hours), default=0)

    cmap = LinearSegmentedColormap.from_list("load", SEQUENTIAL)
    cell_w, cell_h, pad = 1.0, 1.0, 0.08
    for row, day in enumerate(range(7)):
        for col, hour in enumerate(hours):
            value = load[day][hour]
            color = cmap(value / peak) if peak and value else "#f1f0ec"
            ax.add_patch(
                FancyBboxPatch(
                    (col + pad, row + pad), cell_w - 2 * pad, cell_h - 2 * pad,
                    boxstyle="round,pad=0,rounding_size=0.12", facecolor=color, linewidth=0,
                )
            )
            if value:
                light = value / peak > 0.55
                ax.text(
                    col + 0.5, row + 0.52, str(value), ha="center", va="center", fontsize=8.5,
                    color="white" if light else TEXT_PRIMARY, fontweight="bold" if light else "normal",
                )

    ax.set_xlim(0, len(hours))
    ax.set_ylim(7, 0)
    ax.set_xticks([i + 0.5 for i in range(len(hours))], [f"{h}" for h in hours])
    ax.set_yticks([i + 0.5 for i in range(7)], WEEKDAYS_SHORT)
    ax.tick_params(length=0, colors=TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("час начала", color=TEXT_MUTED, fontsize=9)
    return _to_png(fig)


def empty_chart(*, title: str, subtitle: str) -> bytes:
    fig, ax = _figure(title, subtitle)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.text(0.5, 0.5, "Пока нет данных за этот период", ha="center", va="center",
            transform=ax.transAxes, fontsize=12, color=TEXT_MUTED)
    return _to_png(fig)
