from aiogram.types import BufferedInputFile, CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Column
from aiogram_dialog.widgets.text import Const
from dishka.integrations.aiogram_dialog import inject, FromDishka

from src.application.mediator import Mediator
from src.application.use_cases.admin.export_report import (
    REPORT_KIND_LABELS,
    ExportFileDTO,
    ExportReportRequest,
    ReportKind,
)
from src.presentation.telegram.features.admin.states import AdminExportSG


@inject
async def on_export_click(
    callback: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
    mediator: FromDishka[Mediator],
) -> None:
    kind = ReportKind(button.widget_id)
    report: ExportFileDTO = await mediator.handle(ExportReportRequest(kind=kind))
    await callback.answer()
    await callback.message.answer_document(
        BufferedInputFile(report.content, filename=report.filename),
        caption=f"{REPORT_KIND_LABELS[kind]} — строк: {report.rows}",
    )


admin_export_dialog = Dialog(
    Window(
        Const(
            "📥 <b>Выгрузки</b>\n\n"
            "CSV-файлы открываются в Excel/Google Sheets: полные данные для отчётов "
            "и сверки оплат."
        ),
        Column(
            *(
                Button(Const(label), id=kind.value, on_click=on_export_click)
                for kind, label in REPORT_KIND_LABELS.items()
            )
        ),
        Cancel(Const("⬅️ Назад")),
        state=AdminExportSG.main,
    ),
)
