import os

# Configure test env BEFORE importing app modules.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_DEBUG", "true")
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-do-not-use-in-prod-test-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("WHATSAPP_SERVICE_API_KEY", "test-api-key")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import Rol, Sede
from app.services.auth_service import create_user, issue_token


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def db_session(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session, monkeypatch):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    # Ensure settings cached value matches test env.
    get_settings.cache_clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db_session):
    user = create_user(
        db_session,
        email="admin@example.com",
        password="AdminPass!2026",
        nombre="Admin Test",
        rol=Rol.admin.value,
        sede=None,
    )
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def staff_urdesa(db_session):
    user = create_user(
        db_session,
        email="urdesa@example.com",
        password="StaffPass!2026",
        nombre="Staff Urdesa",
        rol=Rol.staff.value,
        sede=Sede.urdesa.value,
    )
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def staff_ciudad_celeste(db_session):
    user = create_user(
        db_session,
        email="celeste@example.com",
        password="StaffPass!2026",
        nombre="Staff Celeste",
        rol=Rol.staff.value,
        sede=Sede.ciudad_celeste.value,
    )
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def token_admin(admin_user):
    return issue_token(admin_user)


@pytest.fixture()
def token_urdesa(staff_urdesa):
    return issue_token(staff_urdesa)


@pytest.fixture()
def token_celeste(staff_ciudad_celeste):
    return issue_token(staff_ciudad_celeste)


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
