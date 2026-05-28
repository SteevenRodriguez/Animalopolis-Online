import logging
import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings

logger = logging.getLogger("animalopolis")


def _safe_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": code, "message": message}})


def register_error_handlers(app: FastAPI) -> None:
    settings = get_settings()

    @app.exception_handler(StarletteHTTPException)
    async def http_exc_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "http_error", "message": exc.detail}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exc_handler(request: Request, exc: RequestValidationError):
        # Strip non-JSON-serializable bits (pydantic v2 puts the raw exception
        # inside ctx, which json.dumps cannot encode).
        clean_details: list[dict] = []
        for err in exc.errors():
            clean = {k: v for k, v in err.items() if k != "ctx"}
            if "ctx" in err:
                clean["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
            clean_details.append(clean)
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Datos inválidos",
                    "details": clean_details,
                }
            },
        )

    @app.exception_handler(IntegrityError)
    async def integrity_exc_handler(request: Request, exc: IntegrityError):
        logger.warning("IntegrityError: %s", exc)
        return _safe_response(409, "integrity_error", "Conflicto de integridad")

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exc_handler(request: Request, exc: SQLAlchemyError):
        logger.error("DB error: %s", exc)
        return _safe_response(500, "db_error", "Error de base de datos")

    @app.exception_handler(Exception)
    async def generic_exc_handler(request: Request, exc: Exception):
        # Never leak stack traces / internals in responses.
        logger.error("Unhandled exception: %s\n%s", exc, traceback.format_exc())
        if settings.APP_ENV != "production" and settings.APP_DEBUG:
            return _safe_response(500, "internal_error", f"{type(exc).__name__}")
        return _safe_response(500, "internal_error", "Error interno del servidor")
