import datetime

from sqlalchemy import select, insert, update, column, text, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class DataInteraction():
    def __init__(self, session: async_sessionmaker):
        self._sessions = session
    pass