from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.api.schemas import FOPInput, FOPResponse, BranchResponse
from app.repositories.fop_repo import FOPRepository
from app.repositories.branch_repo import BranchRepository
from app.repositories.person_repo import PersonRepository
from app.services.address_filter import extract_region, extract_district
from app.services.geocoder import Geocoder
from app.services.branch_finder import BranchFinder
from app.schemas.fop import FOPCreate
from app.schemas.person import PersonCreate

router = APIRouter()

geocoder = Geocoder()

@router.post("/fops/", response_model=FOPResponse)
def create_fop(fop_in: FOPInput, db: Session = Depends(get_db)):
    fop_repo = FOPRepository(db)
    branch_repo = BranchRepository(db)
    person_repo = PersonRepository(db)
    branch_finder = BranchFinder(branch_repo)

    person_schema = PersonCreate(
        first_name=fop_in.first_name,
        last_name=fop_in.last_name,
        middle_name=fop_in.middle_name,
        inn=fop_in.edrpou
    )
    person, _ = person_repo.get_or_create(person_schema)

    region = extract_region(fop_in.address)
    district = extract_district(fop_in.address)

    coords = geocoder.geocode(fop_in.address)
    lat, lon = coords if coords else (None, None)

    nearest_branch = None
    if lat and lon:
        nearest_branch, _ = branch_finder.find_nearest(lat, lon)

    fop_schema = FOPCreate(
        edrpou=fop_in.edrpou,
        name=fop_in.name,
        address=fop_in.address,
        registration_date=fop_in.registration_date,
        activity_type=fop_in.activity_type,
        person_id=person.id,
        nearest_branch_id=nearest_branch.id if nearest_branch else None,
        region=region,
        district=district,
        latitude=lat,
        longitude=lon,
    )

    fop, _ = fop_repo.get_or_create(fop_schema)
    db.refresh(fop)
    
    return fop

@router.get("/branches/", response_model=List[BranchResponse])
def get_branches(db: Session = Depends(get_db)):
    branch_repo = BranchRepository(db)
    return branch_repo.get_all()
