"""industry grade gst upgrades"""

from alembic import op
import sqlalchemy as sa

revision = "0002_industry_upgrade"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sellers", sa.Column("composition_flag", sa.Boolean(), server_default=sa.false(), nullable=False))

    op.create_table(
        "hsn_master",
        sa.Column("code", sa.String(length=8), primary_key=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("default_gst_rate", sa.Float(), nullable=False),
    )

    op.create_table(
        "invoice_sequences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("financial_year", sa.String(length=7), nullable=False),
        sa.Column("state_code", sa.String(length=2), nullable=False),
        sa.Column("current_value", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("financial_year", "state_code", name="uq_invoice_sequence_fy_state"),
    )
    op.create_index(op.f("ix_invoice_sequences_id"), "invoice_sequences", ["id"], unique=False)

    op.add_column("invoices", sa.Column("export_flag", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("invoices", sa.Column("composition_flag", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("invoices", sa.Column("tax_shifted_to_recipient", sa.Boolean(), server_default=sa.false(), nullable=False))

    op.execute("UPDATE invoices SET status = 'DRAFT' WHERE status = 'draft'")
    op.execute("UPDATE invoices SET status = 'FINAL' WHERE status = 'finalized'")
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.create_check_constraint("ck_invoice_status", "status IN ('DRAFT', 'FINAL')")
        batch_op.create_check_constraint("ck_supply_type", "supply_type IN ('intra', 'inter', 'export')")

    op.add_column("invoice_items", sa.Column("hsn_code", sa.String(length=8), nullable=True))
    op.execute("UPDATE invoice_items SET hsn_code = hsn_sac")
    with op.batch_alter_table("invoice_items") as batch_op:
        batch_op.drop_column("hsn_sac")
        batch_op.alter_column("hsn_code", nullable=False)
        batch_op.create_foreign_key("fk_invoice_items_hsn_code", "hsn_master", ["hsn_code"], ["code"])

    op.create_table(
        "idempotency_keys",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    with op.batch_alter_table("invoice_items") as batch_op:
        batch_op.add_column(sa.Column("hsn_sac", sa.String(length=12), nullable=True))
    op.execute("UPDATE invoice_items SET hsn_sac = hsn_code")
    with op.batch_alter_table("invoice_items") as batch_op:
        batch_op.drop_constraint("fk_invoice_items_hsn_code", type_="foreignkey")
        batch_op.drop_column("hsn_code")
        batch_op.alter_column("hsn_sac", nullable=False)

    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_constraint("ck_supply_type", type_="check")
        batch_op.drop_constraint("ck_invoice_status", type_="check")
    op.drop_column("invoices", "tax_shifted_to_recipient")
    op.drop_column("invoices", "composition_flag")
    op.drop_column("invoices", "export_flag")

    op.drop_index(op.f("ix_invoice_sequences_id"), table_name="invoice_sequences")
    op.drop_table("invoice_sequences")
    op.drop_table("hsn_master")

    op.drop_column("sellers", "composition_flag")
