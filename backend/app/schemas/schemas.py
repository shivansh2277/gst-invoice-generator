"""Pydantic schemas for API input and output."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

ALLOWED_GST_RATES = {0, 5, 12, 18, 28, 40}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=255)


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str

    class Config:
        from_attributes = True


class SellerBase(BaseModel):
    name: str
    gstin: str = Field(min_length=15, max_length=15)
    address: str
    state_code: str = Field(min_length=2, max_length=2)


class SellerCreate(SellerBase):
    pass


class SellerRead(SellerBase):
    id: int

    class Config:
        from_attributes = True


class BuyerBase(BaseModel):
    name: str
    gstin: Optional[str] = Field(default=None, min_length=15, max_length=15)
    address: str
    state_code: str = Field(min_length=2, max_length=2)


class BuyerCreate(BuyerBase):
    pass


class BuyerRead(BuyerBase):
    id: int

    class Config:
        from_attributes = True


class InvoiceItemCreate(BaseModel):
    name: str
    hsn_sac: str
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    discount: float = Field(default=0, ge=0)
    gst_rate: float

    @field_validator("gst_rate")
    @classmethod
    def validate_rate(cls, value: float) -> float:
        if value not in ALLOWED_GST_RATES:
            raise ValueError("GST rate must be one of 0, 5, 12, 18, 28, 40")
        return value


class InvoiceItemRead(BaseModel):
    id: int
    name: str
    hsn_sac: str
    quantity: float
    unit_price: float
    discount: float
    gst_rate: float
    taxable_value: float
    tax_amount: float
    total_value: float

    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    seller_id: int
    buyer_id: int
    invoice_type: str = Field(pattern="^(B2B|B2C)$")
    reverse_charge: bool = False
    items: list[InvoiceItemCreate]


class TaxSummaryRead(BaseModel):
    total_taxable: float
    total_cgst: float
    total_sgst: float
    total_igst: float
    total_tax: float


class InvoiceRead(BaseModel):
    id: int
    seller_id: int
    buyer_id: int
    invoice_number: str
    invoice_type: str
    reverse_charge: bool
    supply_type: str
    status: str
    total_taxable: float
    total_cgst: float
    total_sgst: float
    total_igst: float
    grand_total: float
    grand_total_words: str
    created_at: datetime
    items: list[InvoiceItemRead]

    class Config:
        from_attributes = True
