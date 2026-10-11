from html import escape

from aiogram_dialog import DialogManager

from src.domain.constants import CONSULTATION_TYPE_LABELS
from src.domain.enums.consultation import ConsultationType


async def consultation_types_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    return {
        "consultation_types": [
            {"id": t.value, "label": label}
            for t, label in CONSULTATION_TYPE_LABELS.items()
        ]
    }


async def consultation_confirm_getter(dialog_manager: DialogManager, **kwargs) -> dict:
    data = dialog_manager.dialog_data
    comment = data.get("comment")
    return {
        "consultation_type": CONSULTATION_TYPE_LABELS[
            ConsultationType(data["consultation_type"])
        ],
        "comment": escape(comment) if comment else "—",
    }
