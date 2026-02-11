"""ORM models for GST invoice generator."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sellers = relationship("Seller", back_populates="owner")


class Seller(Base):
    __tablename__ = "sellers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15), unique=True, nullable=False)
    address = Column(Text, nullable=False)
    state_code = Column(String(2), nullable=False)
    composition_flag = Column(Boolean, default=False, nullable=False)

    owner = relationship("User", back_populates="sellers")
    invoices = relationship("Invoice", back_populates="seller")


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15), nullable=True)
    address = Column(Text, nullable=False)
    state_code = Column(String(2), nullable=False)

    invoices = relationship("Invoice", back_populates="buyer")


class HsnMaster(Base):
    __tablename__ = "hsn_master"

    code = Column(String(8), primary_key=True)
    description = Column(String(255), nullable=False)
    default_gst_rate = Column(Float, nullable=False)


class InvoiceSequence(Base):
    __tablename__ = "invoice_sequences"
    __table_args__ = (UniqueConstraint("financial_year", "state_code", name="uq_invoice_sequence_fy_state"),)

    id = Column(Integer, primary_key=True, index=True)
    financial_year = Column(String(7), nullable=False)
    state_code = Column(String(2), nullable=False)
    current_value = Column(Integer, default=0, nullable=False)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key = Column(String(128), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_hash = Column(String(64), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT', 'FINAL')", name="ck_invoice_status"),
        CheckConstraint("supply_type IN ('intra', 'inter', 'export')", name="ck_supply_type"),
    )

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("sellers.id"), nullable=False)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    invoice_type = Column(String(3), nullable=False)
    reverse_charge = Column(Boolean, default=False, nullable=False)
    export_flag = Column(Boolean, default=False, nullable=False)
    composition_flag = Column(Boolean, default=False, nullable=False)
    tax_shifted_to_recipient = Column(Boolean, default=False, nullable=False)
    supply_type = Column(String(10), nullable=False)
    status = Column(String(20), default="DRAFT", nullable=False)
    total_taxable = Column(Float, default=0.0, nullable=False)
    total_cgst = Column(Float, default=0.0, nullable=False)
    total_sgst = Column(Float, default=0.0, nullable=False)
    total_igst = Column(Float, default=0.0, nullable=False)
    grand_total = Column(Float, default=0.0, nullable=False)
    grand_total_words = Column(String(255), default="", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    seller = relationship("Seller", back_populates="invoices")
    buyer = relationship("Buyer", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    tax_summary = relationship("TaxSummary", back_populates="invoice", uselist=False, cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    name = Column(String(255), nullable=False)
    hsn_code = Column(String(8), ForeignKey("hsn_master.code"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)
    gst_rate = Column(Float, nullable=False)
    taxable_value = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)

    invoice = relationship("Invoice", back_populates="items")


class TaxSummary(Base):
    __tablename__ = "tax_summary"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), unique=True, nullable=False)
    total_taxable = Column(Float, nullable=False)
    total_cgst = Column(Float, nullable=False)
    total_sgst = Column(Float, nullable=False)
    total_igst = Column(Float, nullable=False)
    total_tax = Column(Float, nullable=False)

    invoice = relationship("Invoice", back_populates="tax_summary")
