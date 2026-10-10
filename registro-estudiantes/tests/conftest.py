"""Fixtures de pytest.

Se intenta usar MySQL real (como en CI con service container); si no hay
un servidor disponible, se hace fallback a SQLite en memoria. El engine
de la app se decide ANTES de importar `app.database` para que la app y
las pruebas usen siempre la misma base.
"""
import os

from sqlalchemy import create_engine, text
import pytest

_mysql_url = os.environ.get("DATABASE_URL", "")
_use_mysql = False
if _mysql_url.startswith("mysql"):
    try:  # ¿hay un MySQL real disponible?
        _probe = create_engine(_mysql_url, pool_pre_ping=True)
        with _probe.connect() as c:
            c.execute(text("SELECT 1"))
        _use_mysql = True
    except Exception:
        _use_mysql = False

if not _use_mysql:
    # Fuerza sqlite en memoria para app Y pruebas.
    os.environ["DATABASE_URL"] = "sqlite://"
    _mysql_url = "sqlite://"

# Importar la app DESPUÉS de fijar la URL de base de datos.
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

if _use_mysql:
    test_engine = create_engine(_mysql_url, pool_pre_ping=True)
else:
    test_engine = create_engine(
        _mysql_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

TestingSession = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def crear_tablas():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def cliente():
    # Sin `with`: evita disparar el lifespan real (que usaría la BD de prod).
    yield TestClient(app, raise_server_exceptions=True)


@pytest.fixture()
def estudiante_base():
    return {
        "nombre": "María",
        "apellido": "González",
        "ci": "4812345",
        "carrera": "Ingeniería Informática",
        "semestre": 5,
        "email": "maria.gonzalez@uni.edu",
        "estado": "activo",
        "materias": ["Programación I", "Matemática I"],
        "contacto": {
            "telefono": "+595981123456",
            "direccion": "Av. Mcal. López 1234, Asunción",
        },
    }
