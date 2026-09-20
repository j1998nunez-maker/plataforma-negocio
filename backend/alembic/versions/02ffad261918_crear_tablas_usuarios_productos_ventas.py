"""crear tablas usuarios productos ventas

Revision ID: 02ffad261918
Revises: 
Create Date: 2026-09-20 15:31:26.514518

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02ffad261918'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Este archivo es una "migración": una receta con pasos exactos para crear
# (upgrade) o deshacer (downgrade) las tablas en PostgreSQL. Alembic guarda
# un historial de estas recetas para que cualquier base de datos nueva
# (tu laptop, un servidor, la del cliente piloto) pueda llegar al mismo
# estado ejecutando: alembic upgrade head


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre_completo", sa.String(length=150), nullable=False),
        sa.Column("correo", sa.String(length=150), nullable=False),
        sa.Column("contrasena_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "rol IN ('dueno', 'contador', 'vendedor')", name="ck_usuarios_rol_valido"
        ),
    )
    op.create_index("ix_usuarios_correo", "usuarios", ["correo"], unique=True)

    op.create_table(
        "productos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(length=150), nullable=False),
        sa.Column("categoria", sa.String(length=80), nullable=True),
        sa.Column("precio_venta", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock_actual", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "fecha_creacion",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_productos_nombre", "productos", ["nombre"])

    op.create_table(
        "ventas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "producto_id",
            sa.Integer(),
            sa.ForeignKey("productos.id"),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
        ),
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("precio_unitario", sa.Numeric(10, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "fecha_venta",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_ventas_producto_id", "ventas", ["producto_id"])
    op.create_index("ix_ventas_usuario_id", "ventas", ["usuario_id"])
    op.create_index("ix_ventas_fecha_venta", "ventas", ["fecha_venta"])


def downgrade() -> None:
    op.drop_table("ventas")
    op.drop_table("productos")
    op.drop_index("ix_usuarios_correo", table_name="usuarios")
    op.drop_table("usuarios")
