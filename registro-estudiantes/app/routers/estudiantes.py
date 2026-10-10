"""Router CRUD + búsquedas: cubre las 10 funcionalidades del proyecto.

IMPORTANTE: las rutas estáticas (/buscar, /filtro, /materia) van ANTES
de /{estudiante_id} para que FastAPI no interprete "buscar" como un id.
"""
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])

ESTADOS_VALIDOS = ("activo", "inactivo", "egresado", "suspendido")


def _get_estudiante_or_404(estudiante_id: int, db: Session) -> models.Estudiante:
    estudiante = db.get(models.Estudiante, estudiante_id)
    if estudiante is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un estudiante con _id={estudiante_id}",
        )
    return estudiante


# ------------------------------------------------------------------
# 1. Registrar un nuevo estudiante
# ------------------------------------------------------------------
@router.post(
    "",
    response_model=schemas.EstudianteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo estudiante",
)
def crear_estudiante(payload: schemas.EstudianteCreate, db: Session = Depends(get_db)):
    # Validación previa de CI y email duplicados para dar errores claros
    for campo, valor in (("ci", payload.ci), ("email", payload.email)):
        existe = db.query(models.Estudiante).filter(
            getattr(models.Estudiante, campo) == valor
        ).first()
        if existe:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un estudiante con {campo}='{valor}'",
            )
    estudiante = models.Estudiante(**payload.model_dump())
    db.add(estudiante)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de unicidad: la CI o el email ya están registrados",
        ) from exc
    db.refresh(estudiante)
    return estudiante


# ------------------------------------------------------------------
# 2. Listar todos los estudiantes
# ------------------------------------------------------------------
@router.get(
    "",
    response_model=list[schemas.EstudianteOut],
    summary="Listar todos los estudiantes",
)
def listar_estudiantes(db: Session = Depends(get_db)):
    return db.query(models.Estudiante).order_by(models.Estudiante.id).all()


# ------------------------------------------------------------------
# 6. Buscar por nombre, apellido o CI  (ruta estática: va antes de /{id})
# ------------------------------------------------------------------
@router.get(
    "/buscar",
    response_model=list[schemas.EstudianteOut],
    summary="Buscar estudiantes por nombre, apellido o CI",
)
def buscar_estudiantes(
    q: str = Query(..., min_length=2, max_length=100,
                   description="Texto a buscar en nombre, apellido o CI"),
    db: Session = Depends(get_db),
):
    patron = f"%{q.strip()}%"
    resultados = (
        db.query(models.Estudiante)
        .filter(
            (models.Estudiante.nombre.like(patron))
            | (models.Estudiante.apellido.like(patron))
            | (models.Estudiante.ci.like(patron))
        )
        .all()
    )
    return resultados


# ------------------------------------------------------------------
# 7, 8, 9. Filtros: carrera / semestre / estado  (ruta estática)
# ------------------------------------------------------------------
@router.get(
    "/filtro",
    response_model=list[schemas.EstudianteOut],
    summary="Filtrar estudiantes por carrera, semestre y/o estado académico",
)
def filtrar_estudiantes(
    carrera: str | None = Query(None, max_length=100),
    semestre: int | None = Query(None, ge=1, le=12),
    estado: str | None = Query(None, description="activo | inactivo | egresado | suspendido"),
    db: Session = Depends(get_db),
):
    if estado is not None and estado not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"estado inválido: use uno de {list(ESTADOS_VALIDOS)}",
        )
    query = db.query(models.Estudiante)
    if carrera:
        query = query.filter(func.lower(models.Estudiante.carrera)
                             == carrera.strip().lower())
    if semestre is not None:
        query = query.filter(models.Estudiante.semestre == semestre)
    if estado is not None:
        query = query.filter(models.Estudiante.estado == estado)
    return query.all()


# ------------------------------------------------------------------
# 10. Consultar estudiantes que tengan registrada una determinada materia
#     (JSON_CONTAINS busca dentro de la columna JSON `materias`)
# ------------------------------------------------------------------
def _filtrar_por_materia(db: Session, materia: str) -> list[models.Estudiante]:
    """Busca la materia dentro de la columna JSON `materias`.

    - MySQL: JSON_CONTAINS (búsqueda en el servidor, eficiente).
    - SQLite (tests locales sin servidor): filtro en Python.
    """
    if db.bind.dialect.name == "mysql":
        return (
            db.query(models.Estudiante)
            .filter(text("JSON_CONTAINS(estudiantes.materias, JSON_QUOTE(:m)) = 1"))
            .params(m=materia)
            .all()
        )
    return [
        e
        for e in db.query(models.Estudiante).all()
        if materia in (e.materias or [])
    ]


@router.get(
    "/materia",
    response_model=list[schemas.EstudianteOut],
    summary="Consultar estudiantes que tengan registrada una determinada materia",
)
def estudiantes_por_materia(
    materia: str = Query(..., min_length=3, max_length=100,
                         examples=["Programación I"]),
    db: Session = Depends(get_db),
):
    return _filtrar_por_materia(db, materia.strip())


# ------------------------------------------------------------------
# 3. Consultar un estudiante mediante su identificador
# ------------------------------------------------------------------
@router.get(
    "/{estudiante_id}",
    response_model=schemas.EstudianteOut,
    summary="Consultar un estudiante por su identificador (_id)",
)
def obtener_estudiante(estudiante_id: int, db: Session = Depends(get_db)):
    return _get_estudiante_or_404(estudiante_id, db)


# ------------------------------------------------------------------
# 4. Modificar la información de un estudiante (PUT completo / PATCH parcial)
# ------------------------------------------------------------------
@router.put(
    "/{estudiante_id}",
    response_model=schemas.EstudianteOut,
    summary="Modificar toda la información de un estudiante",
)
def reemplazar_estudiante(
    estudiante_id: int,
    payload: schemas.EstudianteCreate,
    db: Session = Depends(get_db),
):
    estudiante = _get_estudiante_or_404(estudiante_id, db)
    for campo, valor in payload.model_dump().items():
        setattr(estudiante, campo, valor)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de unicidad: la CI o el email ya pertenecen a otro estudiante",
        ) from exc
    db.refresh(estudiante)
    return estudiante


@router.patch(
    "/{estudiante_id}",
    response_model=schemas.EstudianteOut,
    summary="Modificar parcialmente la información de un estudiante",
)
def actualizar_estudiante(
    estudiante_id: int,
    payload: schemas.EstudianteUpdate,
    db: Session = Depends(get_db),
):
    estudiante = _get_estudiante_or_404(estudiante_id, db)
    datos = payload.model_dump(exclude_unset=True)
    if not datos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe enviar al menos un campo a modificar",
        )
    for campo, valor in datos.items():
        setattr(estudiante, campo, valor)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflicto de unicidad: la CI o el email ya pertenecen a otro estudiante",
        ) from exc
    db.refresh(estudiante)
    return estudiante


# ------------------------------------------------------------------
# 5. Eliminar un estudiante
# ------------------------------------------------------------------
@router.delete(
    "/{estudiante_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar un estudiante",
)
def eliminar_estudiante(estudiante_id: int, db: Session = Depends(get_db)):
    estudiante = _get_estudiante_or_404(estudiante_id, db)
    datos = estudiante.to_dict()
    db.delete(estudiante)
    db.commit()
    return {"mensaje": "Estudiante eliminado correctamente", "estudiante": datos}
