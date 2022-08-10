"""empty message

Revision ID: ef493a5aed7f
Revises: 4a9dc6be945f
Create Date: 2022-08-10 09:44:51.773449

"""
from alembic import op
import sqlalchemy as sa

# This is needed for the Web2PyBoolean class.
import bookserver.models


# revision identifiers, used by Alembic.
revision = "ef493a5aed7f"
down_revision = "4a9dc6be945f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "assignments",
        sa.Column(
            "peer_async_visible",
            bookserver.models.Web2PyBoolean(length=1),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column("assignments", "is_peer")
