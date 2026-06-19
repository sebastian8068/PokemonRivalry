from typing import Annotated, AsyncGenerator
from fastapi import Depends
from dotenv import load_dotenv
from os import getenv
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()


def _get_env(key: str) -> str:
    value = getenv(key)
    if not value:
        raise ValueError(f"{key} is not defined in .env file")
    return value


DB_HOST = _get_env("DB_HOST")
DB_USER = _get_env("DB_USER")
DB_PASSWORD = _get_env("DB_PASSWORD")
DB_NAME = _get_env("DB_NAME")

DB_DRIVER = getenv(key="DB_DRIVER", default="mariadb+mariadbconnector")
DB_ECHO = getenv(key="DB_ECHO", default="false").lower() == "true"


URL_CONNECTION = URL.create(
    drivername=DB_DRIVER,
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database=DB_NAME,
    query={"charset": "utf8mb4"},
)

engine = create_async_engine(
    URL_CONNECTION,
    echo=DB_ECHO,
    pool_size=10,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
    pool_timeout=30,
)

SessionDep = async_sessionmaker(
    autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionDep() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]
