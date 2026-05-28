import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models._mixins import TimestampsMixin, UUIDPkMixin


class Alta(UUIDPkMixin, TimestampsMixin, Base):
    __tablename__ = "altas"
    __table_args__ = (
        CheckConstraint("consentimiento = true", name="consentimiento_check"),
        CheckConstraint(
            "sede IN ('urdesa','ciudad_celeste')", name="sede_check"
        ),
        CheckConstraint(
            "estado_envio IN ('pendiente','enviado','fallido')",
            name="estado_envio_check",
        ),
        Index("ix_altas_sede_estado_created", "sede", "estado_envio", "created_at"),
        Index("ix_altas_fecha_atencion", "fecha_atencion"),
    )

    sede: Mapped[str] = mapped_column(String(32), nullable=False)
    mascota_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("mascotas.id"), nullable=False
    )
    propietario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("propietarios.id"), nullable=False
    )
    fecha_atencion: Mapped[date] = mapped_column(Date, nullable=False)
    tipo_consulta: Mapped[str] = mapped_column(String(32), nullable=False)
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
