"""Official letters: drafts, signatories, signature & seal images

Revision ID: 027_official_letters
Revises: 026_expenses_inventory
Create Date: 2026-10-14

New tables letter_images, official_letters, letter_signatories and their
enum types. Nothing existing is changed.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "027_official_letters"
down_revision: Union[str, None] = "026_expenses_inventory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: each type is created once, explicitly, below (see 014).
letter_kind = postgresql.ENUM(
    "GENERAL", "APPOINTMENT", "MEMBERSHIP_CERTIFICATE", "SERVICE_CERTIFICATE", "TO_WHOM_IT_MAY_CONCERN",
    "DONATION_ACKNOWLEDGEMENT", "NOC", "INVITATION", name="letterkind", create_type=False)
letter_status = postgresql.ENUM("DRAFT", "AWAITING_SIGNATURES", "ISSUED", "REVOKED", name="letterstatus",
                                create_type=False)
signatory_role = postgresql.ENUM("SIGNATORY", "ATTESTOR", name="signatoryrole", create_type=False)
signatory_status = postgresql.ENUM("PENDING", "SIGNED", "PAPER", "DECLINED", name="signatorystatus",
                                   create_type=False)
image_kind = postgresql.ENUM("SIGNATURE", "SEAL", name="letterimagekind", create_type=False)
ENUMS = (letter_kind, letter_status, signatory_role, signatory_status, image_kind)


def _timestamps():
    """created_at / updated_at, which app.models.base.Base gives every table."""
    return (sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))


def _user_fk(name: str) -> sa.Column:
    return sa.Column(name, sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in ENUMS:
        enum.create(bind, checkfirst=True)

    op.create_table(
        "letter_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", image_kind, nullable=False, index=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("temple_members.id", ondelete="SET NULL"),
                  nullable=True, index=True),
        sa.Column("data", sa.LargeBinary(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        _user_fk("uploaded_by"),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        *_timestamps(),
    )
    op.create_table(
        "official_letters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference_number", sa.String(30), nullable=True, unique=True),
        sa.Column("verify_token", sa.String(40), nullable=False),
        sa.Column("kind", letter_kind, nullable=False),
        sa.Column("status", letter_status, nullable=False, server_default="DRAFT"),
        sa.Column("letter_date", sa.Date(), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("recipient_name", sa.String(200), nullable=True),
        sa.Column("recipient_address", sa.Text(), nullable=True),
        sa.Column("salutation", sa.String(100), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("closing", sa.String(100), nullable=True),
        sa.Column("include_seal", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("seal_image_id", sa.Integer(), sa.ForeignKey("letter_images.id", ondelete="SET NULL"),
                  nullable=True),
        _user_fk("created_by"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("issued_at", sa.DateTime(), nullable=True),
        _user_fk("issued_by"),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        _user_fk("revoked_by"),
        sa.Column("revoke_reason", sa.String(500), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_official_letters_verify_token", "official_letters", ["verify_token"], unique=True)
    op.create_index("ix_official_letters_status", "official_letters", ["status"])
    op.create_table(
        "letter_signatories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("letter_id", sa.Integer(), sa.ForeignKey("official_letters.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("temple_members.id", ondelete="SET NULL"),
                  nullable=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("designation", sa.String(100), nullable=True),
        sa.Column("role", signatory_role, nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("status", signatory_status, nullable=False),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        _user_fk("signed_by"),
        sa.Column("signed_ip", sa.String(64), nullable=True),
        sa.Column("signature_image_id", sa.Integer(), sa.ForeignKey("letter_images.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("decline_reason", sa.String(500), nullable=True),
        _user_fk("marked_by"),
        *_timestamps(),
        sa.UniqueConstraint("letter_id", "member_id", name="uq_letter_signatory_member"),
    )


def downgrade() -> None:
    op.drop_table("letter_signatories")
    op.drop_index("ix_official_letters_status", table_name="official_letters")
    op.drop_index("ix_official_letters_verify_token", table_name="official_letters")
    op.drop_table("official_letters")
    op.drop_table("letter_images")
    bind = op.get_bind()
    for enum in ENUMS:
        enum.drop(bind, checkfirst=True)
