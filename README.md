# Animalópolis Online

Sistema interno de captura de datos, exámenes y consulta para la clínica veterinaria
Animalópolis. Fase 1 (MVP): backend FastAPI + Postgres + S3 (MinIO en dev) + dashboard React.
El envío por WhatsApp lo gestiona un sistema externo que consume la API REST documentada.

## Estado actual

Construido hasta el momento (Partes 1–2 de 4):

**Parte 1 — backend, base de datos y auth/roles**
- Backend FastAPI con estructura modular (routers / schemas / services / core / storage).
- Postgres + SQLAlchemy 2.0 + Alembic con migración inicial.
- Autenticación JWT, hashing argon2id, roles **admin / staff** con sistema de capabilities extensible.
- Endpoints de autenticación, usuarios (admin) y altas (con RBAC y aislamiento por sede).
- Endpoints `/envios/...` protegidos por **`X-API-Key`** para el sistema externo de WhatsApp.
- Rate limit en login, headers de seguridad básicos, errores sin leaks.

**Parte 2 — integración S3**
- `S3StorageBackend` real con boto3, compatible con AWS S3, Cloudflare R2 y MinIO (mismo código, distinto endpoint).
- `POST /api/v1/examenes` (multipart): subida a S3, solo `storage_key` + metadatos en DB.
- Validación de archivos: tipo permitido, tamaño máximo, **magic bytes** (detecta spoofing de MIME).
- Listado y detalle de exámenes con RBAC (staff sólo su sede; admin todas).
- `GET /api/v1/examenes/{id}/file-url` → URL firmada temporal (5 min por defecto).
- `/envios/examenes/{pendientes,file-url,marcar-enviado}` para el sistema externo.
- Rate limit en upload.
- Tests con **moto** simulando S3 (bucket privado verificado).

**Parte 3 — frontend React**
- Vite + TypeScript + Tailwind + TanStack Query + React Router + react-hook-form + zod.
- Login con persistencia de token y auto-logout en 401.
- Dashboard con dos tabs: Altas y Exámenes.
- Listados paginados con filtros (sede para admin, fecha, estado de envío).
- Vistas de detalle de alta y examen; botón "Ver archivo" que pide la URL firmada al backend y la abre en pestaña nueva.
- Formularios con validación cliente (zod) + servidor; staff queda forzado a su sede.
- Input de WhatsApp con hint de código de país; el backend normaliza a E.164.
- Carga de archivo con validación cliente de tipo y tamaño antes de subir.
- Responsive (tablet/celular).

**Parte 4 — suite completa de pruebas (backend)**
- **147 tests** verdes en ~15s, **90.5 % de cobertura** del paquete `app/`.
- `tests/unit/`: WhatsApp E.164, validación de archivos por magic bytes, matriz de capabilities, consentimiento obligatorio en todas sus formas.
- `tests/integration/`: auth, altas, exámenes, listados con filtros, paginación, presigned URL, ciclo de envío externo, capa S3 con moto.
- `tests/security/`:
  - **RBAC** en todos los endpoints protegidos (sin token, token inválido/tamper/expirado, staff vs otra sede, staff en endpoints admin).
  - **JWT**: firma incorrecta, algoritmo `none`, `sub` faltante/no-UUID, usuario desactivado, usuario inexistente.
  - **SQL injection**: payloads clásicos en login, filtros y body — todos rechazados sin 500.
  - **Subida de archivos**: HTML, SVG, ZIP, ELF disfrazados; path traversal en filenames; storage_key no contiene input del usuario; el bucket no recibe nada cuando la validación falla.
  - **Hashing**: argon2id verificado, hashes únicos por salt, contraseñas nunca aparecen en respuestas ni dumps de DB.
  - **Error leakage**: 4xx/5xx jamás incluyen stacktrace, paths, secretos, fragmentos SQL, ni distinguen "email no existe" de "contraseña incorrecta".
  - **Security headers**: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` en todas las respuestas (incluido errores).
  - **CORS**: origen no permitido NO recibe `Access-Control-Allow-Origin`; con `Access-Control-Allow-Credentials: true` nunca se combina con `*`.
  - **Presigned URL**: contiene `X-Amz-Signature` + `X-Amz-Expires` ≤ 1h; cada URL apunta a un único objeto; cliente anónimo (sin firma) no puede leer el bucket.
  - **Rate limit**: login bombardeado devuelve 429 antes de los 15 intentos.

## Estructura

```
backend/        FastAPI + SQLAlchemy + Alembic
  app/          código fuente
  alembic/      migraciones
  tests/        unit / integration / security
frontend/       React + Vite + TypeScript + Tailwind + TanStack Query
  src/api       cliente axios (interceptor JWT, manejo 401)
  src/auth      AuthContext + ProtectedRoute
  src/pages     login, dashboard, listados, detalles, formularios
  src/components componentes compartidos (table, paginación, file upload, etc.)
docker-compose.yml
```

## Deploy en producción

Ver **[DEPLOY.md](DEPLOY.md)**: servidor propio con Docker, `docker-compose.prod.yml`
(frontend compilado servido por nginx, Caddy con HTTPS automático, Postgres y MinIO
en red interna), backups y checklist de seguridad.

## Cómo correrlo localmente

### Opción A: con Docker (recomendado)

```bash
cp .env.example .env                    # editar APP_SECRET_KEY y WHATSAPP_SERVICE_API_KEY
docker compose up --build
```

Disponibles:
- **Frontend**: <http://localhost:5173>
- API: <http://localhost:8000>
- Docs Swagger: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- MinIO consola: <http://localhost:9001> (user: `minioadmin` / pass: `minioadmin`)
- Postgres: `localhost:5432` (`animalopolis` / `animalopolis`)

Al primer arranque se crea automáticamente un admin con las credenciales de
`BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD` definidas en `docker-compose.yml`
(`admin@animalopolis.app` / `ChangeMeNow!2026`). **Cambia esa contraseña tras el primer login.**

### Opción B: sin Docker

Backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env                    # editar valores
# Asegúrate de tener Postgres corriendo en la URL configurada
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
cp .env.example .env                    # ajusta VITE_API_URL si tu backend no está en :8000
npm run dev                             # http://localhost:5173
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

# 8. Subir un examen (multipart). Acepta application/pdf, image/{jpeg,png,webp}.
curl -s -X POST http://localhost:8000/api/v1/examenes \
  -H "Authorization: Bearer $TOKEN" \
  -F "sede=urdesa" \
  -F "nombre_mascota=Firulais" \
  -F "nombre_propietario=Juan Perez" \
  -F "whatsapp=+593991234567" \
  -F "tipo_examen=sangre" \
  -F "consentimiento=true" \
  -F "file=@/ruta/al/examen.pdf;type=application/pdf"

# 9. Obtener URL firmada (válida unos minutos)
curl -s http://localhost:8000/api/v1/examenes/<ID>/file-url \
  -H "Authorization: Bearer $TOKEN"

# 10. Sistema externo: examenes pendientes + URL firmada + marcar enviado
curl -s http://localhost:8000/api/v1/envios/examenes/pendientes \
  -H "X-API-Key: dev-api-key-change-me"

curl -s http://localhost:8000/api/v1/envios/examenes/<ID>/file-url \
  -H "X-API-Key: dev-api-key-change-me"

curl -s -X POST http://localhost:8000/api/v1/envios/examenes/<ID>/marcar-enviado \
  -H "X-API-Key: dev-api-key-change-me"
```

## Validación de archivos

La carga de exámenes valida en este orden y rechaza si algo falla:

1. **Tamaño**: ≤ `MAX_UPLOAD_SIZE_BYTES` (default 15 MiB; configurable en `.env`).
2. **Tipo declarado**: MIME debe estar en `ALLOWED_UPLOAD_MIME`
   (`application/pdf`, `image/jpeg`, `image/png`, `image/webp`).
3. **Magic bytes**: el contenido real debe corresponder al MIME declarado.
   Un PDF con cabecera `MZ` (ejecutable) o un EXE con `Content-Type: image/png`
   se rechaza con 422 — no llega a S3.

El archivo se sube a S3 con la key `examenes/{sede}/{yyyy}/{mm}/{uuid}.{ext}`.
**En la base de datos solo se guarda esa key + metadatos** (nombre original,
mime, tamaño), nunca el archivo en sí.

## Bucket S3 / R2

- El bucket es **privado**: solo el backend con credenciales puede subir/leer.
- El frontend y el sistema externo nunca tocan el bucket directamente; obtienen
  una URL firmada vía la API (válida `S3_PRESIGNED_EXPIRES_SECONDS`, default 300s).
- Para migrar de MinIO a AWS S3 o Cloudflare R2: cambiar las 5 variables
  `S3_*` en el `.env`. **No hay que tocar código** — la misma clase `S3StorageBackend`
  habla con los tres.

## Correr tests

```bash
cd backend
pip install -e ".[dev]"          # si no lo hiciste

# Suite completa (147 tests, ~15s)
pytest

# Por categoría
pytest tests/unit -v             # validaciones puras, sin DB ni HTTP
pytest tests/integration -v      # endpoints + storage (SQLite + moto S3)
pytest tests/security -v         # RBAC, JWT, SQLi, headers, leaks, presigned URL

# Coverage
pytest --cov --cov-report=term-missing
pytest --cov --cov-report=html   # luego abre htmlcov/index.html
```

Los tests usan **SQLite en memoria + moto** (mock de S3). No requieren Postgres
ni MinIO en marcha — todo el harness corre aislado y sin red. La sesión de DB
se recrea por cada test (rollback total entre tests).

Cobertura actual del paquete `app/`: **90.5 %**. Líneas no cubiertas:
admin user CRUD (PATCH/DELETE — no expuesto por el frontend en MVP) y
bootstrap_admin (corre solo en startup real, no en tests).

## Roles y permisos

| Capability             | admin | staff                       |
|------------------------|:-----:|:---------------------------:|
| Alta — crear           |   ✓   | ✓ (solo su sede)            |
| Alta — leer todas      |   ✓   | —                           |
| Alta — leer su sede    |   —   | ✓                           |
| Alta — marcar enviado  |   ✓   | —                           |
| Examen — crear         |   ✓   | ✓ (solo su sede)            |
| Examen — leer          |   ✓   | ✓ (solo su sede)            |
| Examen — descargar     |   ✓   | ✓ (solo su sede)            |
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
