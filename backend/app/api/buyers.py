"""Buyer endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Buyer, User
from app.schemas.schemas import BuyerCreate, BuyerRead
from app.utils.gst import is_valid_gstin, state_code_from_gstin

router = APIRouter(prefix="/buyers", tags=["buyers"])


@router.post("", response_model=BuyerRead)
def create_buyer(
    payload: BuyerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Buyer:
    """Create buyer profile."""
    if payload.gstin:
        if not is_valid_gstin(payload.gstin):
            raise HTTPException(status_code=400, detail="Invalid GSTIN format")
        if state_code_from_gstin(payload.gstin) != payload.state_code:
            raise HTTPException(status_code=400, detail="GSTIN state code mismatch")
    buyer = Buyer(**payload.model_dump())
    db.add(buyer)
    db.commit()
    db.refresh(buyer)
    return buyer


@router.get("", response_model=list[BuyerRead])
def list_buyers(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[Buyer]:
    """List buyers."""
    return db.query(Buyer).all()
