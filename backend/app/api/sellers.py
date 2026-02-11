"""Seller endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Seller, User
from app.schemas.schemas import SellerCreate, SellerRead
from app.utils.gst import is_valid_gstin, state_code_from_gstin

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.post("", response_model=SellerRead)
def create_seller(
    payload: SellerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Seller:
    """Create seller profile."""
    gstin = payload.gstin.upper()
    state_code = payload.state_code.upper()
    if not is_valid_gstin(gstin):
        raise HTTPException(status_code=400, detail="Invalid GSTIN format")
    if state_code_from_gstin(gstin) != state_code:
        raise HTTPException(status_code=400, detail="GSTIN state code mismatch")
    seller = Seller(**payload.model_dump(), gstin=gstin, state_code=state_code, user_id=current_user.id)
    db.add(seller)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Seller GSTIN already exists") from exc
    db.refresh(seller)
    return seller


@router.get("", response_model=list[SellerRead])
def list_sellers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Seller]:
    """List sellers for current user."""
    return db.query(Seller).filter(Seller.user_id == current_user.id).all()
