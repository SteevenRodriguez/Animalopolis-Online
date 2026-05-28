"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-28

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=32), nullable=False),
        sa.Column("sede", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rol IN ('admin','staff')", name="ck_usuarios_rol_check"),
        sa.CheckConstraint(
            "sede IS NULL OR sede IN ('urdesa','ciudad_celeste')",
            name="ck_usuarios_sede_check",
        ),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
    )
    op.create_index("ix_usuarios_email", "usuarios", ["email"])

    op.create_table(
        "propietarios",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("whatsapp_e164", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("whatsapp_e164", name="uq_propietarios_whatsapp_e164"),
    )

    op.create_table(
        "mascotas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("propietario_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["propietario_id"], ["propietarios.id"],
            ondelete="RESTRICT", name="fk_mascotas_propietario_id_propietarios",
        ),
    )
    op.create_index("ix_mascotas_propietario_nombre", "mascotas", ["propietario_id", "nombre"])

    op.create_table(
        "altas",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("sede", sa.String(length=32), nullable=False),
        sa.Column("mascota_id", sa.Uuid(), nullable=False),
        sa.Column("propietario_id", sa.Uuid(), nullable=False),
        sa.Column("fecha_atencion", sa.Date(), nullable=False),
        sa.Column("tipo_consulta", sa.String(length=32), nullable=False),
        sa.Column("consentimiento", sa.Boolean(), nullable=False),
        sa.Column("estado_envio", sa.String(length=16), nullable=False, server_default="pendiente"),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["mascota_id"], ["mascotas.id"], name="fk_altas_mascota_id_mascotas"),
        sa.ForeignKeyConstraint(["propietario_id"], ["propietarios.id"], name="fk_altas_propietario_id_propietarios"),
        sa.ForeignKeyConstraint(["created_by_id"], ["usuarios.id"], name="fk_altas_created_by_id_usuarios"),
        sa.CheckConstraint("consentimiento = true", name="ck_altas_consentimiento_check"),
        sa.CheckConstraint("sede IN ('urdesa','ciudad_celeste')", name="ck_altas_sede_check"),
        sa.CheckConstraint(
            "estado_envio IN ('pendiente','enviado','fallido')",
            name="ck_altas_estado_envio_check",
        ),
    )
    op.create_index("ix_altas_sede_estado_created", "altas", ["sede", "estado_envio", "created_at"])
    op.create_index("ix_altas_fecha_atencion", "altas", ["fecha_atencion"])

    op.create_table(
        "examenes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("sede", sa.String(length=32), nullable=False),
        sa.Column("mascota_id", sa.Uuid(), nullable=False),
        sa.Column("propietario_id", sa.Uuid(), nullable=False),
        sa.Column("tipo_examen", sa.String(length=32), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("archivo_nombre", sa.String(length=255), nullable=False),
        sa.Column("archivo_mime", sa.String(length=128), nullable=False),
        sa.Column("archivo_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("consentimiento", sa.Boolean(), nullable=False),
        sa.Column("estado_envio", sa.String(length=16), nullable=False, server_default="pendiente"),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["mascota_id"], ["mascotas.id"], name="fk_examenes_mascota_id_mascotas"),
        sa.ForeignKeyConstraint(["propietario_id"], ["propietarios.id"], name="fk_examenes_propietario_id_propietarios"),
        sa.ForeignKeyConstraint(["created_by_id"], ["usuarios.id"], name="fk_examenes_created_by_id_usuarios"),
        sa.CheckConstraint("consentimiento = true", name="ck_examenes_consentimiento_check"),
        sa.CheckConstraint("sede IN ('urdesa','ciudad_celeste')", name="ck_examenes_sede_check"),
        sa.CheckConstraint(
            "estado_envio IN ('pendiente','enviado','fallido')",
            name="ck_examenes_estado_envio_check",
        ),
    )
    op.create_index("ix_examenes_sede_estado_created", "examenes", ["sede", "estado_envio", "created_at"])


def downgrade() -> None:
    op.drop_table("examenes")
    op.drop_table("altas")
    op.drop_table("mascotas")
    op.drop_table("propietarios")
    op.drop_table("usuarios")
