from decimal import Decimal
from html import escape

from dishka.integrations.aiogram_dialog import inject, FromDishka
from aiogram_dialog import DialogManager

from src.application.mediator import Mediator
from src.application.use_cases.client.get_by_id import GetClientByIdRequest
from src.application.use_cases.progress.measurements import GetMeasurementsRequest
from src.domain.entities.client import Client
from src.domain.entities.client_measurement import ClientMeasurement
from src.presentation.telegram.build_media import build_media_attachment
from src.presentation.telegram.charts import render
from src.presentation.telegram.charts.media import chart_media

RECENT_IN_SUMMARY = 6
WEIGHT_CHART = "weight"
GIRTH_CHART = "girth"


def _fmt(value: Decimal) -> str:
    # 76.0 → «76», 72.5 → «72.5»
    return f"{value.normalize():f}"


def _delta(first: Decimal, last: Decimal) -> str:
    diff = last - first
    if diff == 0:
        return "без изменений"
    sign = "+" if diff > 0 else "−"
    return f"{sign}{_fmt(abs(diff))}"


def _entry_line(m: ClientMeasurement) -> str:
    parts = []
    if m.weight is not None:
        parts.append(f"{_fmt(m.weight)} кг")
    for title, value in (("талия", m.waist), ("грудь", m.chest), ("бёдра", m.hips)):
        if value is not None:
            parts.append(f"{title} {_fmt(value)}")
    if m.photo_file_id:
        parts.append("📷")
    return f"{m.measured_on.strftime('%d.%m.%y')} — " + " · ".join(parts)


def _trend(items: list[ClientMeasurement], attr: str) -> tuple[ClientMeasurement, ClientMeasurement] | None:
    known = [m for m in items if getattr(m, attr) is not None]
    if not known:
        return None
    return known[0], known[-1]


async def _load(dialog_manager: DialogManager, mediator: Mediator) -> list[ClientMeasurement]:
    return await mediator.handle(
        GetMeasurementsRequest(client_id=dialog_manager.start_data["client_id"])
    )


@inject
async def progress_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    client: Client = await mediator.handle(
        GetClientByIdRequest(client_id=dialog_manager.start_data["client_id"])
    )
    items = await _load(dialog_manager, mediator)
    as_trainer = dialog_manager.start_data.get("as_trainer", False)
    title = f"📈 <b>Прогресс · {escape(client.full_name)}</b>" if as_trainer else "📈 <b>Мой прогресс</b>"

    lines = [title, ""]
    if not items:
        lines.append(
            "Записей пока нет. Добавьте первый замер — вес и обхваты, "
            "можно с фото «до», чтобы потом было с чем сравнить."
        )
    else:
        weight = _trend(items, "weight")
        if weight:
            first, last = weight
            line = f"⚖️ Вес: <b>{_fmt(last.weight)} кг</b>"
            if first is not last:
                line += f" ({_delta(first.weight, last.weight)} с {first.measured_on.strftime('%d.%m')})"
            lines.append(line)
        girths = []
        for title_, attr in (("Талия", "waist"), ("Грудь", "chest"), ("Бёдра", "hips")):
            trend = _trend(items, attr)
            if trend:
                first, last = trend
                part = f"{title_} {_fmt(getattr(last, attr))}"
                if first is not last:
                    part += f" ({_delta(getattr(first, attr), getattr(last, attr))})"
                girths.append(part)
        if girths:
            lines.append("📏 " + " · ".join(girths) + " см")
        lines.append("\n<b>Последние записи</b>")
        lines.extend(_entry_line(m) for m in reversed(items[-RECENT_IN_SUMMARY:]))

    photos = [m for m in items if m.photo_file_id]
    has_numbers = sum(1 for m in items if any((m.weight, m.waist, m.chest, m.hips))) >= 2
    return {
        "text": "\n".join(lines),
        "has_items": bool(items),
        "has_chart": has_numbers,
        "photos_count": len(photos),
        "has_photos": bool(photos),
    }


@inject
async def chart_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    items = await _load(dialog_manager, mediator)
    kind = dialog_manager.dialog_data.get("chart", WEIGHT_CHART)
    if kind == WEIGHT_CHART:
        series = [render.Series("Вес, кг", [m.weight for m in items], render.BLUE)]
        unit = "кг"
        title = "Вес"
    else:
        series = [
            render.Series("Талия", [m.waist for m in items], render.ORANGE),
            render.Series("Грудь", [m.chest for m in items], render.VIOLET),
            render.Series("Бёдра", [m.hips for m in items], render.AQUA),
        ]
        unit = "см"
        title = "Обхваты"

    # без фото-only записей: у них нет чисел, линия бы зря тянулась по датам
    used = [i for i in range(len(items)) if any(s.values[i] is not None for s in series)]
    dates = [items[i].measured_on for i in used]
    series = [render.Series(s.label, [s.values[i] for i in used], s.color) for s in series]
    has_data = bool(used)
    subtitle = (
        f"{dates[0].strftime('%d.%m.%Y')} – {dates[-1].strftime('%d.%m.%Y')} · замеров: {len(used)}"
        if dates
        else ""
    )

    def draw() -> bytes:
        if not has_data:
            return render.empty_chart(title=title, subtitle="Нет замеров")
        return render.progress_lines(
            title=title, subtitle=subtitle, dates=dates, series=series, unit=unit
        )

    return {
        "chart": await chart_media(draw),
        "caption": f"📊 <b>{title}</b>",
        "is_weight": kind == WEIGHT_CHART,
    }


@inject
async def photos_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    items = await _load(dialog_manager, mediator)
    return {
        "photos": [
            {"id": str(m.id), "label": f"📷 {_entry_line(m).replace(' · 📷', '')}"}
            for m in reversed(items)
            if m.photo_file_id
        ]
    }


@inject
async def photo_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    items = await _load(dialog_manager, mediator)
    item = next(m for m in items if m.id == dialog_manager.dialog_data["photo_id"])
    return {
        "photo": build_media_attachment(item.photo_file_id),
        "caption": _entry_line(item).replace(" · 📷", ""),
    }


@inject
async def delete_confirm_getter(
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
    **kwargs,
) -> dict:
    items = await _load(dialog_manager, mediator)
    return {"entry": _entry_line(items[-1]) if items else "—"}
