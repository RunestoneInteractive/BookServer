"""Merge heads

Revision ID: 217f49a3b6be
Revises: ef493a5aed7f, ee5c9117b71f
Create Date: 2022-11-08 22:12:45.660639

"""
from alembic import op
import sqlalchemy as sa

# This is needed for the Web2PyBoolean class.
import bookserver.models


# revision identifiers, used by Alembic.
revision = "217f49a3b6be"
down_revision = ("ef493a5aed7f", "ee5c9117b71f")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
