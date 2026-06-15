"""initial schema

Bootstraps the full AutoSOC schema from the SQLAlchemy model metadata. Use
``alembic revision --autogenerate`` for subsequent incremental migrations.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-15
"""
from alembic import op

from app.db.base import Base
import app.models  # noqa: F401  populate metadata

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
