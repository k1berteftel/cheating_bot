import datetime

from sqlalchemy import select, insert, update, column, text, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from database.model import UsersTable, AccountsTable


class DataInteraction():
    def __init__(self, session: async_sessionmaker):
        self._sessions = session

    async def check_user(self, user_id: int) -> bool:
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.user_id == user_id))
        return True if result else False

    async def add_user(self, user_id: int):
        if await self.check_user(user_id):
            return
        async with self._sessions() as session:
            await session.execute(insert(UsersTable).values(
                user_id=user_id,
            ))
            await session.commit()

    async def add_account(self, user_id: int, name: str, login: str, password: str, cookies: str):
        async with self._sessions() as session:
            model = AccountsTable(
                user_id=user_id,
                name=name,
                login=login,
                password=password,
                cookies=cookies
            )
            session.add(model)
            await session.commit()

    async def get_user(self, user_id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(UsersTable).where(UsersTable.user_id == user_id))
        return result

    async def get_account(self, id: int):
        async with self._sessions() as session:
            result = await session.scalar(select(AccountsTable).where(AccountsTable.id == id))
        return result

    async def del_account(self, id: int):
        async with self._sessions() as session:
            await session.execute(delete(AccountsTable).where(AccountsTable.id == id))
            await session.commit()

