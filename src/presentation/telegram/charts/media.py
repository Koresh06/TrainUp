import asyncio
import hashlib
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

from aiogram.enums import ContentType
from aiogram_dialog.api.entities import MediaAttachment

CHARTS_DIR = Path(tempfile.gettempdir()) / "trainup_charts"
# графики пересчитываются при каждом открытии — старые файлы не нужны
CHARTS_TTL_SECONDS = 60 * 60


def _cleanup() -> None:
    border = time.time() - CHARTS_TTL_SECONDS
    for file in CHARTS_DIR.glob("*.png"):
        try:
            if file.stat().st_mtime < border:
                file.unlink()
        except OSError:
            pass


def _save(png: bytes) -> Path:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    # имя = хэш содержимого: aiogram_dialog кэширует file_id по пути, поэтому
    # одинаковый график не грузится в Telegram повторно, а изменившийся —
    # гарантированно получает новый путь (иначе показался бы старый file_id)
    path = CHARTS_DIR / f"{hashlib.sha1(png).hexdigest()}.png"
    if path.exists():
        path.touch()  # свежий mtime — очистка не удалит файл, который сейчас показываем
    else:
        path.write_bytes(png)
        _cleanup()
    return path


async def chart_media(render: Callable[[], bytes]) -> MediaAttachment:
    """Рисует график в отдельном потоке (matplotlib блокирующий) и отдаёт
    MediaAttachment для DynamicMedia."""
    path = await asyncio.to_thread(lambda: _save(render()))
    return MediaAttachment(type=ContentType.PHOTO, path=str(path))
