"""temples.upi_vpa - the temple's UPI ID, for the public e-Hundi QR code

Revision ID: 023_temple_upi_vpa
Revises: 022_terms_accepted
Create Date: 2026-09-30

Lets devotees pay directly into the temple's account via any UPI app by
scanning a QR code generated from this VPA - a direct bank-to-bank
transfer, same as the physical Hundi box, never routed through this
backend or a payment gateway.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_temple_upi_vpa"
down_revision: Union[str, None] = "022_terms_accepted"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("temples", sa.Column("upi_vpa", sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column("temples", "upi_vpa")
