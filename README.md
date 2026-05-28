# Animalópolis Online

Sistema interno de captura de datos, exámenes y consulta para la clínica veterinaria
Animalópolis. Fase 1 (MVP): backend FastAPI + Postgres + S3 (MinIO en dev) + dashboard React.
El envío por WhatsApp lo gestiona un sistema externo que consume la API REST documentada.

## Estado actual

Construido en este commit (Parte 1 de 4):

- Backend FastAPI con estructura modular (routers / schemas / services / core / storage).
- Postgres + SQLAlchemy 2.0 + Alembic con migración inicial.
- Autenticación JWT, hashing argon2id, roles **admin / staff** con sistema de capabilities extensible.
- Endpoints de **autenticación** (`/auth/login`, `/auth/me`).
- Endpoints de **usuarios** (admin) y **altas** (con RBAC y aislamiento por sede).
- Endpoints `/envios/...` protegidos por **`X-API-Key`** para el sistema externo de WhatsApp.
- Rate limit en login, headers de seguridad básicos, manejo de errores sin leaks.
- Suite inicial de tests (unit + integración) con SQLite en memoria.
- `docker-compose` con Postgres y MinIO (S3 local, listo para Parte 2).

Pendiente: subida real a S3 (Parte 2), frontend React (Parte 3), suite completa de seguridad (Parte 4).

## Estructura

```
backend/        FastAPI + SQLAlchemy + Alembic
  app/          código fuente
  alembic/      migraciones
  tests/        unit / integration / security
frontend/       (Parte 3)
docker-compose.yml
```

## Cómo correrlo localmente

### Opción A: con Docker (recomendado)

```bash
cp .env.example .env                    # editar APP_SECRET_KEY y WHATSAPP_SERVICE_API_KEY
docker compose up --build
```

Disponibles:
- API: <http://localhost:8000>
- Docs Swagger: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- MinIO consola: <http://localhost:9001> (user: `minioadmin` / pass: `minioadmin`)
- Postgres: `localhost:5432` (`animalopolis` / `animalopolis`)

Al primer arranque se crea automáticamente un admin con las credenciales de
`BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD` definidas en `docker-compose.yml`
(`admin@animalopolis.app` / `ChangeMeNow!2026`). **Cambia esa contraseña tras el primer login.**

### Opción B: sin Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env                    # editar valores
# Asegúrate de tener Postgres corriendo en la URL configurada
alembic upgrade head
uvicorn app.main:app --reload
```

## Probar la Parte 1 manualmente

```bash
# 1. Login
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@animalopolis.app","password":"ChangeMeNow!2026"}'
# -> {"access_token":"...","rol":"admin",...}

TOKEN="<paste-access_token>"

# 2. Quién soy
curl -s http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer $TOKEN"

# 3. Crear staff
curl -s -X POST http://localhost:8000/api/v1/usuarios \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"email":"urdesa@animalopolis.app","password":"StaffPass!2026","nombre":"Vet Urdesa","rol":"staff","sede":"urdesa"}'

# 4. Crear alta como admin (sede libre)
curl -s -X POST http://localhost:8000/api/v1/altas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "sede":"urdesa",
    "nombre_mascota":"Firulais",
    "nombre_propietario":"Juan Perez",
    "whatsapp":"+593991234567",
    "fecha_atencion":"2026-05-28",
    "tipo_consulta":"control",
    "consentimiento":true
  }'

# 5. Listado (admin ve todas las sedes)
curl -s http://localhost:8000/api/v1/altas -H "Authorization: Bearer $TOKEN" | jq

# 6. Como sistema externo: altas pendientes de envío
curl -s http://localhost:8000/api/v1/envios/altas/pendientes \
  -H "X-API-Key: dev-api-key-change-me" | jq

# 7. Marcar como enviada
curl -s -X POST http://localhost:8000/api/v1/envios/altas/<ID>/marcar-enviado \
  -H "X-API-Key: dev-api-key-change-me"
```

## Correr tests

```bash
cd backend
pip install -e ".[dev]"          # si no lo hiciste
pytest                            # corre unit + integration
pytest tests/unit -v
pytest tests/integration -v
```

Los tests usan SQLite en memoria y no requieren Postgres ni MinIO en marcha.

## Roles y permisos

| Capability             | admin | staff                       |
|------------------------|:-----:|:---------------------------:|
| Alta — crear           |   ✓   | ✓ (solo su sede)            |
| Alta — leer todas      |   ✓   | —                           |
| Alta — leer su sede    |   —   | ✓                           |
| Alta — marcar enviado  |   ✓   | —                           |
| Examen — crear         |   ✓   | ✓ (Parte 2)                 |
| Examen — leer          |   ✓   | ✓ (solo su sede, Parte 2)   |
| Examen — descargar     |   ✓   | ✓ (Parte 2)                 |
| Usuarios — gestionar   |   ✓   | —                           |

Añadir un rol nuevo (p.ej. `recepcion`) requiere solo dos cambios:
1. Agregar el valor al enum `Rol` en `app/models/enums.py`.
2. Agregar la fila en `ROLE_CAPABILITIES` en `app/core/permissions.py`.

Ningún endpoint pregunta por rol directamente; todos van por `Capability`, así que
no hace falta refactorizar.

## Modelo de datos (resumen)

```
usuarios         (id, email, password_hash, nombre, rol, sede, is_active)
propietarios     (id, nombre, whatsapp_e164 UNIQUE)
mascotas         (id, nombre, propietario_id)
altas            (id, sede, mascota_id, propietario_id, fecha_atencion,
                  tipo_consulta, consentimiento, estado_envio, enviado_at,
                  created_by_id)
examenes         (id, sede, mascota_id, propietario_id, tipo_examen,
                  storage_key, archivo_nombre, archivo_mime, archivo_size_bytes,
                  consentimiento, estado_envio, enviado_at, created_by_id)
```

Decisiones:
- `propietarios.whatsapp_e164` es único y normalizado a E.164 → permite deduplicar.
- `mascotas` se vincula por `(propietario_id, nombre)`.
- `consentimiento` con `CHECK = true` a nivel DB.
- `storage_key` guarda la clave del objeto en S3/R2; **el archivo nunca se guarda en la DB**.

## Seguridad y variables sensibles

- Todos los secretos vienen de variables de entorno; ver `backend/.env.example`.
- Genera secretos largos:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(64))"   # APP_SECRET_KEY
  python -c "import secrets; print(secrets.token_urlsafe(48))"   # WHATSAPP_SERVICE_API_KEY
  ```
- En producción: configurar `CORS_ORIGINS` con la URL del frontend (nunca `*`).
- En producción: usar IAM keys mínimas para el bucket; bucket **privado**, acceso solo vía URL firmada.
