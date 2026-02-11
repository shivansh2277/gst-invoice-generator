"""HSN master endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import HsnMaster, User
from app.schemas.schemas import HsnMasterRead

router = APIRouter(prefix="/hsn", tags=["hsn"])


@router.get("", response_model=list[HsnMasterRead])
def search_hsn(
    q: str = Query(default="", max_length=20),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[HsnMaster]:
    query = db.query(HsnMaster)
    if q:
        query = query.filter(HsnMaster.code.like(f"{q}%"))
    return query.order_by(HsnMaster.code).limit(20).all()
