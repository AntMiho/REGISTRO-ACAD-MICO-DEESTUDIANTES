"""Configuración de la aplicación.

Las credenciales NUNCA van en el código: se leen desde variables de
entorno (archivo .env en desarrollo, variables en Vercel en producción).
"""
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # URL de conexión MySQL, ej:
    # mysql+pymysql://usuario:password@host:3306/registro_estudiantes
    DATABASE_URL: str = "mysql+pymysql://root:root@localhost:3306/registro_estudiantes"

    # development | production
    ENVIRONMENT: str = "development"

    ADMIN_USER: str = "admin"
    ADMIN_PASSWORD: str = "admin123"

    # En serverless (Vercel) cada lambda crea su pool; mantenerlo pequeño.
    DB_POOL_SIZE: int = 2
    DB_MAX_OVERFLOW: int = 2


settings = Settings()

# Indicador de despliegue en Vercel (las lambdas usan esta variable).
IS_VERCEL = os.environ.get("VERCEL") == "1"
