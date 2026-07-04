from datetime import date

from pydantic import BaseModel, Field

from app.schemas.branch import BranchResponse

class CompanyCreate(BaseModel):

    edrpou: str = Field(..., description="ЄДРПОУ")
    name: str = Field(..., description="Назва")
    legal_form: str | None = Field(None, description="Організаційно-правова форма")
    address: str | None = Field(None, description="Юридична адреса")
    district: str | None = Field(None, description="Район")
    region: str | None = Field(None, description="Область")
    director_name: str | None = Field(None, description="ПІБ директора")
    registration_date: date | None = Field(None, description="Дата реєстрації")
    activity_type: str | None = Field(None, description="Вид діяльності (КВЕД)")
    status: str = Field(default="active", description="Статус")
    latitude: float | None = Field(None, description="Широта")
    longitude: float | None = Field(None, description="Довгота")
    nearest_branch_id: int | None = Field(None, description="FK на найближче відділення")

class CompanyResponse(CompanyCreate):

    id: int
    nearest_branch: BranchResponse | None = None

    model_config = {"from_attributes": True}
