# scripts/check_exists.py
import asyncio
from datetime import date


from src.infrastructure.database.sqlalchemy.connection import async_session_maker
from src.infrastructure.repositories.calendar_slot.sqlalchemy import SQLAlchemyCalendarSlotRepo

async def main():
    async with async_session_maker() as session:
        repo = SQLAlchemyCalendarSlotRepo(session)
        result = await repo.exists_for_date(trainer_id=1, date=date(2026, 8, 12))
        print("exists_for_date(1, 2026-08-12) =", result)


if __name__ == "__main__":
    asyncio.run(main())