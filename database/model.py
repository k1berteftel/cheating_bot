from typing import List
import datetime

from sqlalchemy import BigInteger, VARCHAR, ForeignKey, DateTime, Boolean, Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UsersTable(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    accounts: Mapped[List['AccountsTable']] = relationship('AccountsTable', lazy="selectin", cascade='delete', uselist=True)


class AccountsTable(Base):
    __tablename__ = 'accounts'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.user_id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(VARCHAR)
    login: Mapped[str] = mapped_column(VARCHAR)
    password: Mapped[str] = mapped_column(VARCHAR)
    cookies: Mapped[str] = mapped_column(VARCHAR, default=None, nullable=True)










