from pydantic import BaseModel, Field

class BranchCreate(BaseModel):

    name: str = Field(..., description="Назва відділення")
    address: str = Field(..., description="Адреса")
    city: str | None = Field(None, description="Місто")
    region: str | None = Field(None, description="Область")
    district: str | None = Field(None, description="Район")
    latitude: float | None = Field(None, description="Широта")
    longitude: float | None = Field(None, description="Довгота")
    phone: str | None = Field(None, description="Телефон")
    working_hours: str | None = Field(None, description="Графік роботи")
    branch_type: str | None = Field(None, description="Тип (відділення / банкомат)")

class BranchResponse(BranchCreate):

    id: int

    model_config = {"from_attributes": True}

class BranchWithDistance(BranchResponse):

    distance_km: float = Field(..., description="Відстань у км")
