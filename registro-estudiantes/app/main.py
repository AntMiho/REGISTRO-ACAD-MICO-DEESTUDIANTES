"""Punto de entrada de FastAPI con documentación automática.

- /docs  -> Swagger UI
- /redoc -> ReDoc

La documentación describe cada endpoint, sus parámetros y respuestas
(requisito: "Documentación de las APIs").
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import settings
from .database import Base, engine
from .routers import estudiantes


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Crea la tabla si no existe (idempotente, seguro en Vercel).
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Registro Académico de Estudiantes",
    description=(
        "API REST para administrar información académica de estudiantes: "
        "datos personales, situación académica y materias cursadas.\n\n"
        "**Nota:** el proyecto original pedía MongoDB; esta implementación usa "
        "**MySQL** con SQLAlchemy. La colección `estudiantes` es una sola tabla; "
        "`materias[]` y `contacto{}` se guardan como columnas JSON para mantener "
        "la misma estructura de documento."
    ),
    version="1.0.0",
    contact={"name": "Equipo de desarrollo"},
    lifespan=lifespan,
)

app.include_router(estudiantes.router)


@app.get("/", tags=["General"], include_in_schema=False)
def raiz():
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["General"], summary="Health check")
def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
