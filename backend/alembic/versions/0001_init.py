"""initial schema"""

from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "sellers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("gstin", sa.String(length=15), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("state_code", sa.String(length=2), nullable=False),
    )
    op.create_index(op.f("ix_sellers_id"), "sellers", ["id"], unique=False)

    op.create_table(
        "buyers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("gstin", sa.String(length=15), nullable=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("state_code", sa.String(length=2), nullable=False),
    )
    op.create_index(op.f("ix_buyers_id"), "buyers", ["id"], unique=False)

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("seller_id", sa.Integer(), sa.ForeignKey("sellers.id"), nullable=False),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("buyers.id"), nullable=False),
        sa.Column("invoice_number", sa.String(length=50), nullable=False),
        sa.Column("invoice_type", sa.String(length=3), nullable=False),
        sa.Column("reverse_charge", sa.Boolean(), nullable=False),
        sa.Column("supply_type", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("total_taxable", sa.Float(), nullable=False),
        sa.Column("total_cgst", sa.Float(), nullable=False),
        sa.Column("total_sgst", sa.Float(), nullable=False),
        sa.Column("total_igst", sa.Float(), nullable=False),
        sa.Column("grand_total", sa.Float(), nullable=False),
        sa.Column("grand_total_words", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_invoices_id"), "invoices", ["id"], unique=False)
    op.create_unique_constraint("uq_invoices_invoice_number", "invoices", ["invoice_number"])

    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hsn_sac", sa.String(length=12), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("discount", sa.Float(), nullable=False),
        sa.Column("gst_rate", sa.Float(), nullable=False),
        sa.Column("taxable_value", sa.Float(), nullable=False),
        sa.Column("tax_amount", sa.Float(), nullable=False),
        sa.Column("total_value", sa.Float(), nullable=False),
    )
    op.create_index(op.f("ix_invoice_items_id"), "invoice_items", ["id"], unique=False)

    op.create_table(
        "tax_summary",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("total_taxable", sa.Float(), nullable=False),
        sa.Column("total_cgst", sa.Float(), nullable=False),
        sa.Column("total_sgst", sa.Float(), nullable=False),
        sa.Column("total_igst", sa.Float(), nullable=False),
        sa.Column("total_tax", sa.Float(), nullable=False),
        sa.UniqueConstraint("invoice_id"),
    )
    op.create_index(op.f("ix_tax_summary_id"), "tax_summary", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("tax_summary")
    op.drop_table("invoice_items")
    op.drop_table("invoices")
    op.drop_table("buyers")
    op.drop_table("sellers")
    op.drop_table("users")
