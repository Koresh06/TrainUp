import re
from decimal import Decimal, InvalidOperation

FIELDS = ("weight", "waist", "chest", "hips")
KEYWORDS = {
    "вес": "weight",
    "талия": "waist",
    "грудь": "chest",
    "бедра": "hips",
    "бёдра": "hips",
}
LIMITS = {"weight": (20, 300), "waist": (30, 250), "chest": (30, 250), "hips": (30, 250)}
FIELD_TITLES = {"weight": "Вес", "waist": "Талия", "chest": "Грудь", "hips": "Бёдра"}


def _number(raw: str, field: str) -> Decimal:
    try:
        value = Decimal(raw.replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"Не понял число «{raw}»") from None
    low, high = LIMITS[field]
    if not low <= value <= high:
        raise ValueError(f"{FIELD_TITLES[field]}: {value} — похоже на опечатку")
    return value.quantize(Decimal("0.1"))


def parse_measurement(text: str) -> dict[str, Decimal | None]:
    """
    «72.5» → вес; «72.5 80 95 98» → вес, талия, грудь, бёдра по порядку;
    «-» пропускает значение; можно и словами: «талия 80 вес 72».
    """
    tokens = re.findall(r"[а-яёА-ЯЁ]+|[-\d.,]+", text.lower())
    if not tokens:
        raise ValueError("Отправьте числа, например <code>72.5 80</code>")
    result: dict[str, Decimal | None] = dict.fromkeys(FIELDS)

    if any(t in KEYWORDS for t in tokens):
        it = iter(tokens)
        for token in it:
            field = KEYWORDS.get(token)
            if field is None:
                raise ValueError(f"Не понял «{token}»: вес, талия, грудь, бёдра")
            value = next(it, None)
            if value is None:
                raise ValueError(f"После «{token}» нужно число")
            result[field] = _number(value, field)
    else:
        if len(tokens) > len(FIELDS):
            raise ValueError("Максимум 4 числа: вес, талия, грудь, бёдра")
        for field, token in zip(FIELDS, tokens):
            if token != "-":
                result[field] = _number(token, field)

    if all(v is None for v in result.values()):
        raise ValueError("Нужно хотя бы одно значение")
    return result
