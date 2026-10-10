"""Esquemas Pydantic v2: validaciones de entrada y salida."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

EstadoAcademico = Literal["activo", "inactivo", "egresado", "suspendido"]


class Contacto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    telefono: str = Field(..., min_length=6, max_length=30,
                          examples=["+595 981 123 456"])
    direccion: str = Field(..., min_length=5, max_length=200,
                           examples=["Av. Mcal. López 1234, Asunción"])


class EstudianteBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    ci: str = Field(..., min_length=5, max_length=20,
                    description="Cédula de identidad (única)")
    carrera: str = Field(..., min_length=3, max_length=100)
    semestre: int = Field(..., ge=1, le=12)
    email: EmailStr
    estado: EstadoAcademico = "activo"
    materias: list[str] = Field(default_factory=list)
    contacto: Contacto

    @field_validator("nombre", "apellido", "carrera")
    @classmethod
    def sin_espacios_extra(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("no puede estar vacío")
        return v

    @field_validator("materias")
    @classmethod
    def materias_validas(cls, v: list[str]) -> list[str]:
        limpias = [m.strip() for m in v if m.strip()]
        if len(limpias) != len(v):
            raise ValueError("las materias no pueden ser cadenas vacías")
        return limpias


class EstudianteCreate(EstudianteBase):
    """Payload para POST /estudiantes."""


class EstudianteUpdate(BaseModel):
    """Payload para PUT/PATCH: todos los campos son opcionales."""

    nombre: str | None = Field(None, min_length=2, max_length=100)
    apellido: str | None = Field(None, min_length=2, max_length=100)
    ci: str | None = Field(None, min_length=5, max_length=20)
    carrera: str | None = Field(None, min_length=3, max_length=100)
    semestre: int | None = Field(None, ge=1, le=12)
    email: EmailStr | None = None
    estado: EstadoAcademico | None = None
    materias: list[str] | None = None
    contacto: Contacto | None = None


class EstudianteOut(EstudianteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., serialization_alias="_id")
