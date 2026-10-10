"""Conexión a la base de datos MySQL con SQLAlchemy 2.0.

- Se usa un solo motor y una sola tabla (`estudiantes`), cumpliendo la
  regla de "una sola colección en la Base de Datos" del proyecto.
- `pool_pre_ping` evita conexiones muertas (clave en serverless).
- En Vercel se fuerza `NullPool`: cada lambda abre/cierra su propia
  conexión porque no retiene estado entre invocaciones.
"""
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from .config import IS_VERCEL, settings

_url = make_url(settings.DATABASE_URL)
_is_sqlite = _url.get_backend_name() == "sqlite"
_connect_args = {} if _is_sqlite else {"charset": "utf8mb4"}

if IS_VERCEL:
    # Serverless: sin pool persistente.
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        poolclass=NullPool,
        connect_args=_connect_args,
    )
elif _is_sqlite:
    # Desarrollo/pruebas sin servidor MySQL (conftest fuerza esta ruta).
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        connect_args=_connect_args,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency de FastAPI: una sesión por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
