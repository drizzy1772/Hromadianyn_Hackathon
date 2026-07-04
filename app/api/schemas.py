from pydantic import BaseModel
from datetime import date
from typing import Optional

class FOPInput(BaseModel):
    edrpou: str
    name: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    address: str
    registration_date: date
    activity_type: Optional[str] = None

class BranchResponse(BaseModel):
    id: int
    name: str
    city: Optional[str]
    region: Optional[str]
    district: Optional[str]
    address: str
    latitude: Optional[float]
    longitude: Optional[float]
    phone: Optional[str]
    working_hours: Optional[str]
    branch_type: Optional[str]

    class Config:
        from_attributes = True

class FOPResponse(BaseModel):
    id: int
    edrpou: str
    name: str
    address: str
    region: Optional[str]
    district: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    nearest_branch: Optional[BranchResponse]

    class Config:
        from_attributes = True
