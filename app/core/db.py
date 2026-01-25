
# app/core/database.py

import json
# from datetime import datetime
from datetime import datetime, date

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Optional
from sqlalchemy import (
    text, event, inspect, Column, Integer, String, DateTime, JSON
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker ,Session
from app.core.config import settings  # ensure settings.DATABASE_URL exists

# ---------------------- #
# BASE CONFIG
# ---------------------- #
Base = declarative_base()
DATABASE_URL = settings.DATABASE_URL


# ---------------------- #
# DATABASE MANAGER
# ---------------------- #
class Database:
    def __init__(self) -> None:
        self._engine = create_async_engine(
            DATABASE_URL,
            echo=False,  # Set to True for SQL query logging
            future=True,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    @asynccontextmanager
    async def db_connection(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                print("Database Error >>>", e)
                await session.rollback()
                raise
            finally:
                await session.close()


db_instance = Database()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with db_instance.db_connection() as session:
        yield session

