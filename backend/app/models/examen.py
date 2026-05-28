import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import TimestampsMixin, UUIDPkMixin


class Examen(UUIDPkMixin, TimestampsMixin, Base):
    __tablename__ = "examenes"
    __table_args__ = (
        CheckConstraint("consentimiento = true", name="consentimiento_check"),
        CheckConstraint(
            "sede IN ('urdesa','ciudad_celeste')", name="sede_check"
        ),
        CheckConstraint(
            "estado_envio IN ('pendiente','enviado','fallido')",
            name="estado_envio_check",
        ),
        Index("ix_examenes_sede_estado_created", "sede", "estado_envio", "created_at"),
    )

    sede: Mapped[str] = mapped_column(String(32), nullable=False)
    mascota_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("mascotas.id"), nullable=False
    )
    propietario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propietarios.id"), nullable=False
    )
    tipo_examen: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    archivo_nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    archivo_mime: Mapped[str] = mapped_column(String(128), nullable=False)
    archivo_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    consentimiento: Mapped[bool] = mapped_column(Boolean, nullable=False)
    estado_envio: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pendiente", server_default="pendiente"
    )
    enviado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usuarios.id"), nullable=True
    )
