from pydantic import BaseModel, Field

class PersonCreate(BaseModel):

    first_name: str = Field(..., description="Ім'я")
    last_name: str = Field(..., description="Прізвище")
    middle_name: str | None = Field(None, description="По-батькові")
    inn: str | None = Field(None, description="ІПН")
    address: str | None = Field(None, description="Адреса проживання")
    district: str | None = Field(None, description="Район")
    region: str | None = Field(None, description="Область")
    city: str | None = Field(None, description="Місто")
    phone: str | None = Field(None, description="Телефон")
    email: str | None = Field(None, description="Email")

class PersonResponse(PersonCreate):

    id: int

    model_config = {"from_attributes": True}
