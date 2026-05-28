import uuid

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampsMixin, UUIDPkMixin


class Mascota(UUIDPkMixin, TimestampsMixin, Base):
    __tablename__ = "mascotas"
    __table_args__ = (Index("ix_mascotas_propietario_nombre", "propietario_id", "nombre"),)

    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    propietario_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("propietarios.id", ondelete="RESTRICT"),
        nullable=False,
    )

    propietario: Mapped["Propietario"] = relationship(back_populates="mascotas")  # noqa: F821
