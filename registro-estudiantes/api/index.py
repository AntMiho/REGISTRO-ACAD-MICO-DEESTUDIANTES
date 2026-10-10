"""Handler serverless para Vercel (Python runtime)."""
import os

# Vercel inyecta VERCEL=1; asegurar que se vea antes de importar la app.
os.environ.setdefault("VERCEL", "1")

from app.main import app  # noqa: E402

# Vercel busca la variable `app` en este archivo.
handler = app
