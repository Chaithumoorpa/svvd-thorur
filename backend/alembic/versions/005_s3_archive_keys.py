"""S3 archive keys for generated seva ticket / donation receipt PDFs

Revision ID: 005_s3_archive
Revises: 004_v2_core
Create Date: 2026-09-21

Adds nullable columns recording the S3 object key of the most recently
archived PDF for a ticket/receipt. Populated on next generation; existing
rows are left null (no S3-stored copy exists for them yet).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_s3_archive"
down_revision: Union[str, None] = "004_v2_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("seva_tickets", sa.Column("pdf_s3_key", sa.String(), nullable=True))
    op.add_column("donations", sa.Column("receipt_s3_key", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("donations", "receipt_s3_key")
    op.drop_column("seva_tickets", "pdf_s3_key")
