# personal_soft_test
# 📌 Proyecto API de Mensajes

API construida con **FastAPI** para la gestión de usuarios y mensajes.  
Incluye autenticación JWT, limitación de tasa con Redis, y pruebas automatizadas con `pytest`.

---

## 🚀 Características principales

- **Usuarios**:
  - Crear, actualizar y eliminar usuarios (borrado lógico).
  - Obtener usuarios por ID, usuario actual (`/users/me`) o listado completo.
- **Autenticación**:
  - Login con **OAuth2 + JWT** (`/token`).
  - Tokens con expiración configurada en `.env`.
- **Mensajes**:
  - Creación y consulta de mensajes en sesiones.
  - Filtros por remitente, límite y offset.
- **Seguridad**:
  - Middleware de **Rate Limiting con Redis**.
  - JWT con algoritmo configurable (`HS256` por defecto).
- **Pruebas unitarias**:
  - Implementadas con `pytest` y base de datos SQLite en memoria.

---

## 🛠️ Tecnologías usadas

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/) (basado en SQLAlchemy y Pydantic)
- [Redis](https://redis.io/) (para limitación de tasa)
- [Docker Compose](https://docs.docker.com/compose/)
- [JWT (python-jose)](https://python-jose.readthedocs.io/en/latest/)
- [Pytest](https://docs.pytest.org/)

---

## 📂 Estructura del proyecto

 app/
│── main.py # Punto de entrada FastAPI
│── config.py # Configuración centralizada (usa .env)
│── database.py # Conexión y creación de tablas
│── models.py # Modelos SQLModel
│── schemas.py # Esquemas Pydantic
│── crud.py # Operaciones de base de datos
│── services.py # Lógica de negocio (mensajes)
│── middlewares/
│ └── rate_limit.py # Middleware de Rate Limiting con Redis
tests/
│── test_users.py # Pruebas de usuarios
│── test_auth.py # Pruebas de autenticación
│── test_messages.py # Pruebas de mensajes
docker-compose.yml # Servicios FastAPI + Redis
requirements.txt # Dependencias
.env.example # Variables de entorno (ejemplo)
---

## ⚙️ Configuración

### 1. Variables de entorno (`.env`)
Crea un archivo `.env` en la raíz:

```env
# Base de datos
DATABASE_URL=sqlite:///./database.db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Seguridad
SECRET_KEY=tu_hash_secreto
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate limiting
RATE_LIMIT=100
RATE_LIMIT_WINDOW=60

⚠️ el archivo .env no fue subido a GitHub. Usa local_env.txt como plantilla.

```

2. Levantar servicios con Docker Compose
```
	docker-compose up --build
```

Esto ejecutará:

	FastAPI en http://localhost:8000

	Redis en localhost:6379

🧪 Pruebas

Ejecutar pruebas unitarias con:
```
	pytest -v
```
Las pruebas incluyen:

Creación y autenticación de usuarios.

Validación de tokens JWT.

Lógica de mensajes.

Verificación de rate limiting con Redis.

📚 Documentación interactiva

Una vez levantado el servidor:

Swagger UI

ReDoc

📌 Próximos pasos

Integrar Socket.IO para notificaciones en tiempo real.

Añadir soporte para PostgreSQL en lugar de SQLite.

Despliegue automatizado con GitHub Actions + IaC (CloudFormation/Terraform).