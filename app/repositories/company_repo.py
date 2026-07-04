import logging

from sqlalchemy.orm import Session, joinedload

from app.db.models import LegalEntity
from app.schemas.company import CompanyCreate

logger = logging.getLogger(__name__)

class CompanyRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, company_data: CompanyCreate) -> LegalEntity:
        
        company = LegalEntity(**company_data.model_dump())
        self.db.add(company)
        self.db.flush()
        logger.debug(f"Створено юр. особу: {company.name} (ЄДРПОУ: {company.edrpou})")
        return company

    def get_by_id(self, company_id: int) -> LegalEntity | None:
        
        return (
            self.db.query(LegalEntity)
            .options(joinedload(LegalEntity.nearest_branch))
            .filter(LegalEntity.id == company_id)
            .first()
        )

    def get_by_edrpou(self, edrpou: str) -> LegalEntity | None:
        
        return (
            self.db.query(LegalEntity)
            .filter(LegalEntity.edrpou == edrpou)
            .first()
        )

    def get_all(self) -> list[LegalEntity]:
        
        return (
            self.db.query(LegalEntity)
            .options(joinedload(LegalEntity.nearest_branch))
            .all()
        )

    def get_by_district(self, district: str) -> list[LegalEntity]:
        
        return (
            self.db.query(LegalEntity)
            .filter(LegalEntity.district.ilike(f"%{district}%"))
            .options(joinedload(LegalEntity.nearest_branch))
            .all()
        )

    def update_nearest_branch(
        self, company_id: int, branch_id: int
    ) -> LegalEntity | None:
        
        company = (
            self.db.query(LegalEntity)
            .filter(LegalEntity.id == company_id)
            .first()
        )
        if company:
            company.nearest_branch_id = branch_id
            self.db.flush()
            logger.debug(
                f"Оновлено відділення для {company.name}: branch_id={branch_id}"
            )
        return company

    def update_coordinates(
        self, company_id: int, latitude: float, longitude: float
    ) -> LegalEntity | None:
        
        company = (
            self.db.query(LegalEntity)
            .filter(LegalEntity.id == company_id)
            .first()
        )
        if company:
            company.latitude = latitude
            company.longitude = longitude
            self.db.flush()
        return company

    def get_or_create(self, company_data: CompanyCreate) -> tuple[LegalEntity, bool]:
        
        existing = self.get_by_edrpou(company_data.edrpou)
        if existing:
            return existing, False

        company = self.create(company_data)
        return company, True

    def count(self) -> int:
        
        return self.db.query(LegalEntity).count()
