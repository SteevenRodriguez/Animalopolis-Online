# Deploy en producción (servidor propio + Docker)

Arquitectura: todo corre en un solo servidor con `docker-compose.prod.yml`.
Solo **Caddy** expone puertos (80/443) y maneja HTTPS automático con Let's Encrypt.

```
Internet ──► Caddy (80/443) ─► https://DOMAIN
              ├─ /api/*, /docs              ─► backend (FastAPI :8000)
              ├─ /animalopolis-examenes/*   ─► MinIO (:9000, bucket privado)
              └─ resto                      ─► frontend (nginx, build estático)
              backend ─► postgres (red interna de Docker)
```

Las URLs firmadas que genera el backend (`/animalopolis-examenes/...`) las abre
el navegador (botón "Ver archivo") y el sistema externo de WhatsApp; Caddy las
enruta a MinIO. El bucket sigue siendo privado: sin firma válida, MinIO rechaza todo.

## 1. Requisitos en el servidor

- Linux (Ubuntu 22.04/24.04 recomendado), 2 GB RAM mínimo.
- Puertos 80 y 443 abiertos en el firewall.
- Docker + plugin compose:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # cerrar sesión y volver a entrar
docker compose version
```

## 2. DNS

Cuando tengas el dominio, crea **un registro A** apuntando a la IP pública del
servidor (apex o el subdominio que prefieras). MinIO se sirve por path en el
mismo dominio (`/animalopolis-examenes/*`), así que no necesita registro propio.

Espera a que propaguen (`dig app.tudominio.com` debe devolver la IP) antes de
levantar Caddy, o Let's Encrypt fallará al emitir el certificado (reintenta solo, pero tarda).

## 3. Código y configuración

```bash
git clone <URL-del-repo> animalopolis && cd animalopolis
cp .env.prod.example .env
nano .env
```

Completa **todas** las variables. Genera secretos así:

```bash
openssl rand -base64 48   # uno distinto para cada secreto
```

- `DOMAIN`: el del paso 2 (sin `https://`).
- `ACME_EMAIL`: tu email (avisos de Let's Encrypt).
- `APP_SECRET_KEY`, `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD`,
  `WHATSAPP_SERVICE_API_KEY`, `BOOTSTRAP_ADMIN_PASSWORD`: secretos únicos y largos.
- `WHATSAPP_SERVICE_API_KEY` es la clave que usará el sistema externo de
  WhatsApp en el header `X-API-Key`; compártela solo con ese sistema.

## 4. Levantar

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f backend   # ver migraciones + bootstrap admin
```

Verificación:

```bash
curl https://app.tudominio.com/health     # {"status":"ok","env":"production"}
```

Luego entra a `https://app.tudominio.com`, haz login con
`BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD` y **cambia la contraseña**.
Prueba subir un examen y abrir "Ver archivo" (verifica la URL firmada).

## 5. Operación

### Actualizar a una nueva versión

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Las migraciones de Alembic corren automáticamente al arrancar el backend.

### Logs y estado

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f caddy
```

### Backups (¡importante!)

Hay dos cosas que respaldar: la base de datos y los archivos de MinIO.

```bash
# Base de datos (dump comprimido)
docker exec animalopolis-postgres pg_dump -U animalopolis animalopolis | gzip > backup-db-$(date +%F).sql.gz

# Archivos de exámenes (volumen de MinIO)
docker run --rm -v animalopolis-online_minio-data:/data -v "$PWD":/backup alpine \
  tar czf /backup/backup-minio-$(date +%F).tar.gz -C /data .
```

Automatiza con cron (ej. diario a las 3 AM) y **copia los backups fuera del
servidor** (otro equipo, otro bucket, etc.). Restaurar DB:

```bash
gunzip -c backup-db-YYYY-MM-DD.sql.gz | docker exec -i animalopolis-postgres psql -U animalopolis animalopolis
```

> Nota: si el directorio del proyecto no se llama `animalopolis-online`, ajusta el
> prefijo del volumen (`docker volume ls` para ver el nombre real).

### Modo temporal sin dominio (HTTP por IP)

Mientras no haya dominio se puede correr todo por IP en HTTP plano usando el
override `docker-compose.ip.yml` (usa `deploy/Caddyfile.ip`; las URLs firmadas
de MinIO también pasan por Caddy en el puerto 80, enrutadas por el path del bucket):

```bash
# .env: define SERVER_IP=<ip-publica>
docker compose -f docker-compose.prod.yml -f docker-compose.ip.yml up -d --build
```

App: `http://<ip>` · API: `http://<ip>/docs`. **Sin HTTPS** — no lo uses con
datos reales más tiempo del necesario.

**Cambio a dominio + HTTPS** cuando lo tengas:

1. Crea los registros DNS del paso 2 y abre el puerto 443 en el firewall/security group.
2. En `.env` completa `DOMAIN` y `ACME_EMAIL` reales.
3. Relanza solo con el archivo de producción:

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.ip.yml down
docker compose -f docker-compose.prod.yml up -d --build
```

## 6. Checklist de seguridad post-deploy

- [ ] Contraseña del admin bootstrap cambiada tras el primer login.
- [ ] `.env` solo legible por tu usuario (`chmod 600 .env`).
- [ ] Firewall: solo 22 (SSH), 80 y 443 abiertos.
- [ ] SSH con llave, no contraseña (`PasswordAuthentication no`).
- [ ] Backups automáticos corriendo y probados (restaura uno de prueba).
- [ ] `https://app.../docs` funciona — si no quieres Swagger público, se puede
      bloquear en el Caddyfile quitando `/docs /redoc /openapi.json` del matcher `@api`.
