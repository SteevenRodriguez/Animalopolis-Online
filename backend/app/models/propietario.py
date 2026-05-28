from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models._mixins import TimestampsMixin, UUIDPkMixin


class Propietario(UUIDPkMixin, TimestampsMixin, Base):
    __tablename__ = "propietarios"

    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    whatsapp_e164: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)

    mascotas: Mapped[list["Mascota"]] = relationship(  # noqa: F821
        back_populates="propietario"
    )
