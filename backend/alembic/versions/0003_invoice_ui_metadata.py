"""invoice ui metadata fields"""

from alembic import op
import sqlalchemy as sa

revision = "0003_invoice_ui_metadata"
down_revision = "0002_industry_upgrade"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("logo_base64", sa.Text(), nullable=True))
    op.add_column("invoices", sa.Column("terms_conditions", sa.Text(), nullable=False, server_default=""))
    op.add_column("invoices", sa.Column("signature_name", sa.String(length=120), nullable=False, server_default="Authorized Signatory"))


def downgrade() -> None:
    op.drop_column("invoices", "signature_name")
    op.drop_column("invoices", "terms_conditions")
    op.drop_column("invoices", "logo_base64")
