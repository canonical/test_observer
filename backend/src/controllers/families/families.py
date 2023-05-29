from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.data_access.models import Family
from src.data_access.setup import get_db

from .models import FamilyDTO

router = APIRouter()


@router.get("/{family_name}", response_model=FamilyDTO)
def read_snap_family(family_name: str, db: Session = Depends(get_db)):
    """Retrieve all the stages and artefacts from the snap family"""
    family = db.query(Family).filter(Family.name == family_name).first()
    if family is None:
        raise HTTPException(status_code=404, detail="Family not found")

    family.stages = sorted(family.stages, key=lambda x: x.position)
    return family
