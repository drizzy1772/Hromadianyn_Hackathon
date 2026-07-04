from datetime import date

from pydantic import BaseModel, Field

from app.schemas.branch import BranchResponse

class FOPFromJSON(BaseModel):

    edrpou: str = Field(..., description="ЄДРПОУ / ІПН")
    name: str = Field(..., description="Назва ФОП")
    first_name: str = Field(..., description="Ім'я")
    last_name: str = Field(..., description="Прізвище")
    middle_name: str | None = Field(None, description="По-батькові")
    address: str = Field(..., description="Адреса реєстрації")
    registration_date: date | None = Field(None, description="Дата реєстрації")
    activity_type: str | None = Field(None, description="Вид діяльності (КВЕД)")

class FOPCreate(BaseModel):

    person_id: int = Field(..., description="FK на фізичну особу")
    edrpou: str | None = Field(None, description="ЄДРПОУ / ІПН")
    name: str = Field(..., description="Назва ФОП")
    registration_date: date | None = Field(None, description="Дата реєстрації")
    activity_type: str | None = Field(None, description="Вид діяльності")
    address: str | None = Field(None, description="Адреса реєстрації")
    district: str | None = Field(None, description="Район")
    region: str | None = Field(None, description="Область")
    status: str = Field(default="active", description="Статус")
    latitude: float | None = Field(None, description="Широта")
    longitude: float | None = Field(None, description="Довгота")
    nearest_branch_id: int | None = Field(None, description="FK на найближче відділення")

class FOPResponse(FOPCreate):

    id: int
    nearest_branch: BranchResponse | None = None

    model_config = {"from_attributes": True}
