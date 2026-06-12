"""Add audit_log table; allow 'consulta' rol; index on resource lookups.

Revision ID: 0002_consulta_audit_patch
Revises: 0001_initial
Create Date: 2026-06-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_consulta_audit_patch"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Allow the new 'consulta' role in the CHECK constraint.
    op.drop_constraint("ck_usuarios_rol_check", "usuarios", type_="check")
    op.create_check_constraint(
        "ck_usuarios_rol_check",
        "usuarios",
        "rol IN ('admin','staff','consulta')",
    )

    # 2) Append-only audit_log table.
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("user_rol", sa.String(length=32), nullable=True),
        sa.Column("user_sede", sa.String(length=32), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=32), nullable=True),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["usuarios.id"],
            ondelete="SET NULL", name="fk_audit_log_user_id_usuarios",
        ),
    )
    op.create_index("ix_audit_log_timestamp", "audit_log", ["timestamp"])
    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_resource", "audit_log", ["resource_type", "resource_id"])
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_index("ix_audit_log_resource", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_index("ix_audit_log_timestamp", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_constraint("ck_usuarios_rol_check", "usuarios", type_="check")
    op.create_check_constraint(
        "ck_usuarios_rol_check",
        "usuarios",
        "rol IN ('admin','staff')",
    )
