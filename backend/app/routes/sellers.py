from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import SellerSubscription
from app.schemas import SellerSubscriptionCreate, SellerSubscriptionResponse
from app.utils.deps import get_current_admin
from app.services.scraper import run_scraper

router = APIRouter(prefix="/api/sellers", tags=["sellers"])

@router.post("/trigger-update")
def trigger_update(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin)
):
    try:
        run_scraper(db)
        return {"status": "success", "message": "All mother subscriptions updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SellerSubscriptionResponse)
def create_seller_sub(
    data: SellerSubscriptionCreate, 
    db: Session = Depends(get_db), 
    current_admin: str = Depends(get_current_admin)
):
    exists = db.query(SellerSubscription).filter(SellerSubscription.url == data.url).first()
    if exists:
        raise HTTPException(status_code=400, detail="Seller subscription already exists")
    
    seller = SellerSubscription(name=data.name, url=data.url)
    db.add(seller)
    db.commit()
    db.refresh(seller)
    return seller

@router.get("/", response_model=List[SellerSubscriptionResponse])
def get_seller_subs(
    db: Session = Depends(get_db), 
    current_admin: str = Depends(get_current_admin)
):
    return db.query(SellerSubscription).all()

@router.delete("/{seller_id}")
def delete_seller_sub(
    seller_id: int, 
    db: Session = Depends(get_db), 
    current_admin: str = Depends(get_current_admin)
):
    seller = db.query(SellerSubscription).filter(SellerSubscription.id == seller_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller subscription not found")
    
    db.delete(seller)
    db.commit()
    return {"message": "Seller subscription deleted successfully"}