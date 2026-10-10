# 📚 Registro Académico de Estudiantes — API REST (FastAPI + MySQL)

API REST desarrollada con **FastAPI** y **MySQL** (SQLAlchemy) que permite
administrar información académica de estudiantes: datos personales, situación
académica y materias cursadas.

> **Nota sobre la base de datos:** el enunciado original pedía MongoDB; este
> proyecto implementa el mismo modelo con **MySQL**. La "colección"
> `estudiantes` es **una sola tabla** (requisito del proyecto) y los campos
> anidados `materias[]` y `contacto{}` se guardan como **columnas JSON de
> MySQL**, conservando la misma estructura de documento.

## 🗂️ Estructura del documento (`estudiantes`)

| Campo       | Tipo MySQL          | Descripción                                  |
|-------------|---------------------|----------------------------------------------|
| `_id`       | INT AUTO_INCREMENT  | Identificador único (PK)                     |
| `nombre`    | VARCHAR(100)        | Nombres del estudiante                       |
| `apellido`  | VARCHAR(100)        | Apellidos del estudiante                     |
| `ci`        | VARCHAR(20) UNIQUE  | Cédula de identidad (única)                  |
| `carrera`   | VARCHAR(100)        | Carrera que cursa                            |
| `semestre`  | INT (1–12)          | Semestre actual                              |
| `email`     | VARCHAR(150) UNIQUE | Correo institucional                         |
| `estado`    | VARCHAR(20)         | `activo` · `inactivo` · `egresado` · `suspendido` |
| `materias`  | JSON (array)        | Materias cursadas, ej: `["Programación I"]`  |
| `contacto`  | JSON (objeto)       | `{"telefono": "...", "direccion": "..."}`    |

## ⚙️ Funcionalidades (las 10 requeridas)

| # | Funcionalidad | Método y ruta |
|---|---------------|---------------|
| 1 | Registrar un nuevo estudiante | `POST /estudiantes` |
| 2 | Listar todos los estudiantes | `GET /estudiantes` |
| 3 | Consultar por identificador | `GET /estudiantes/{_id}` |
| 4 | Modificar información (completo / parcial) | `PUT` / `PATCH /estudiantes/{_id}` |
| 5 | Eliminar un estudiante | `DELETE /estudiantes/{_id}` |
| 6 | Buscar por nombre, apellido o CI | `GET /estudiantes/buscar?q=...` |
| 7 | Filtrar por carrera | `GET /estudiantes/filtro?carrera=...` |
| 8 | Filtrar por semestre | `GET /estudiantes/filtro?semestre=...` |
| 9 | Filtrar por estado académico | `GET /estudiantes/filtro?estado=...` |
| 10 | Consultar por materia cursada | `GET /estudiantes/materia?materia=...` |

> Las rutas estáticas (`/buscar`, `/filtro`, `/materia`) están definidas
> **antes** de `/{estudiante_id}` para que FastAPI no las interprete como id.

## 🚀 Puesta en marcha (local)

```bash
# 1. Clonar e ingresar
git clone https://github.com/TU_USUARIO/registro-estudiantes.git
cd registro-estudiantes

# 2. Entorno virtual + dependencias
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Crear la base de datos MySQL
mysql -u root -p -e "CREATE DATABASE registro_estudiantes CHARACTER SET utf8mb4;"

# 4. Configurar variables de entorno
cp .env.example .env            # editar con tus credenciales reales

# 5. Ejecutar en desarrollo
uvicorn app.main:app --reload
```

La documentación interactiva queda en:

- **Swagger UI** → [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc** → [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Ejemplo de payload (POST /estudiantes)

```json
{
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
    "direccion": "Av. Mcal. López 1234, Asunción"
  }
}
```

## 🔐 Manejo de `.env`

- El archivo real **`.env` está en `.gitignore`** y nunca se sube a GitHub.
- `.env.example` sirve como plantilla: se copia a `.env` y se completan los
  valores.
- La cadena de conexión **solo se lee de variables de entorno**
  (`pydantic-settings`), nunca está hardcodeada.
- En Vercel las variables se cargan en *Settings → Environment Variables*
  (`DATABASE_URL`, `ENVIRONMENT`, etc.).

## ☁️ Despliegue en Vercel

Vercel es **serverless**: no puede conectarse a un MySQL local. Se necesita un
MySQL **hosteado externamente**:

1. Crear una base de datos MySQL gratuita en **Aiven**, **Railway** o un
   servicio compatible (PlanetScale-style).
2. Copiar la URL de conexión con formato:
   `mysql+pymysql://usuario:password@host:3306/dbname`
3. En Vercel → *Import Project* → seleccionar el repo.
4. En *Settings → Environment Variables* agregar `DATABASE_URL` (y opcionalmente
   `ENVIRONMENT=production`).
5. Deploy. `vercel.json` enruta todo a `api/index.py` (handler de FastAPI).

Consideraciones serverless (ya implementadas en `app/database.py`):

- `pool_pre_ping=True` para descartar conexiones caídas.
- `NullPool` en Vercel: cada invocación abre y cierra su propia conexión.
- `Base.metadata.create_all()` en el *startup* crea la tabla si no existe.

## 🔄 Flujo de trabajo con Git y GitHub

Se usa el flujo visto en clases (GitHub Flow con rama de desarrollo):

```
main        ← rama protegida, solo se actualiza vía Pull Request
develop     ← integración continua del equipo
feature/*   ← ramas de trabajo
```

```bash
git checkout develop
git checkout -b feature/filtro-materias   # 1. crear rama de trabajo
# ... commits atómicos con mensajes descriptivos ...
git push origin feature/filtro-materias   # 2. subir rama
# 3. Abrir Pull Request hacia develop y pedir revisión
# 4. Merge con revisión aprobada; luego develop → main por PR
```

Reglas: commits pequeños y descriptivos, PR con descripción, nunca push
directo a `main`.

## 🤖 GitHub Actions (CI)

`.github/workflows/ci.yml` se ejecuta en cada `push` y `pull_request` hacia
`main`/`develop`:

1. Levanta un contenedor de servicio **MySQL 8.0**.
2. Instala las dependencias de `requirements.txt`.
3. Corre la suite completa con **pytest**.

Si alguna prueba falla, el PR se marca en rojo y el merge queda bloqueado.

## ✅ Validaciones y manejo de errores

- **Pydantic v2**: `EmailStr` (email válido), `semestre` entre 1 y 12,
  `estado` con valores restringidos (`Literal`), `contacto` obligatorio con
  `telefono` y `direccion`, sin campos extra (`extra="forbid"`).
- **Unicidad en la base de datos**: `ci` y `email` con restricción `UNIQUE`.
- Códigos de error HTTP consistentes:
  - `404` — estudiante no encontrado
  - `409` — CI o email duplicado
  - `422` — datos inválidos (Pydantic devuelve el detalle del campo)

## 🧪 Pruebas

`tests/test_estudiantes.py` cubre las 10 funcionalidades + validaciones:

```bash
pytest -v
```

Si no hay MySQL disponible localmente, la suite cae automáticamente a SQLite
en memoria para poder correr en cualquier máquina.

## 📁 Estructura del proyecto

```
registro-estudiantes/
├── api/
│   └── index.py              # Handler serverless para Vercel
├── app/
│   ├── __init__.py
│   ├── config.py             # Variables de entorno (pydantic-settings)
│   ├── database.py           # Motor SQLAlchemy + sesión
│   ├── main.py               # App FastAPI + documentación
│   ├── models.py             # Modelo ORM (tabla única `estudiantes`)
│   ├── schemas.py            # Validaciones Pydantic v2
│   └── routers/
│       └── estudiantes.py    # Los 10 endpoints
├── tests/
│   ├── conftest.py
│   └── test_estudiantes.py
├── .github/workflows/ci.yml  # GitHub Actions (pytest + MySQL)
├── .env.example              # Plantilla de configuración
├── .gitignore                # Excluye .env, venv, __pycache__, etc.
├── requirements.txt
├── vercel.json
└── README.md
```

---

*Nota: el enunciado mencionaba un repositorio de ejemplo como referencia, pero
el enlace no llegó; la estructura sigue la organización estándar de un
proyecto FastAPI con despliegue en Vercel.*
