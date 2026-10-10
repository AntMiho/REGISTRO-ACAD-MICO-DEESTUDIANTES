"""Modelo ORM: UNA sola tabla `estudiantes`.

Equivalente a la "colección" del enunciado (originalmente MongoDB):
- `materias` y `contacto` se guardan como columnas JSON de MySQL para
  conservar la misma estructura de documento que pide el proyecto.
- `ci` es único: la base de datos rechaza duplicados.
"""
from sqlalchemy import JSON, Column, Integer, String, UniqueConstraint

from .database import Base


class Estudiante(Base):
    __tablename__ = "estudiantes"
    __table_args__ = (
        UniqueConstraint("ci", name="uq_estudiantes_ci"),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )

    # _id: entero autoincremental como identificador. En MySQL la columna
    # se llama `_id`, pero el atributo Python es `id` (Pydantic no serializa
    # atributos que empiezan con underscore).
    id = Column("_id", Integer, primary_key=True, autoincrement=True, index=True)
    nombre = Column(String(100), nullable=False, index=True)
    apellido = Column(String(100), nullable=False, index=True)
    ci = Column(String(20), nullable=False, index=True)
    carrera = Column(String(100), nullable=False, index=True)
    semestre = Column(Integer, nullable=False, index=True)
    email = Column(String(150), nullable=False, unique=True)
    estado = Column(String(20), nullable=False, index=True, default="activo")
    # Array de materias cursadas, ej: ["Programación I", "Matemática I"]
    materias = Column(JSON, nullable=False, default=list)
    # Objeto de contacto: {"telefono": "...", "direccion": "..."}
    contacto = Column(JSON, nullable=False, default=dict)

    def to_dict(self) -> dict:
        return {
            "_id": self.id,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "ci": self.ci,
            "carrera": self.carrera,
            "semestre": self.semestre,
            "email": self.email,
            "estado": self.estado,
            "materias": self.materias or [],
            "contacto": self.contacto or {},
        }
