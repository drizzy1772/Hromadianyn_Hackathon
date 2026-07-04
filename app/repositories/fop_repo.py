import logging

from sqlalchemy.orm import Session, joinedload

from app.db.models import FOP
from app.schemas.fop import FOPCreate

logger = logging.getLogger(__name__)

class FOPRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, fop_data: FOPCreate) -> FOP:
        
        fop = FOP(**fop_data.model_dump())
        self.db.add(fop)
        self.db.flush()
        logger.debug(f"Створено ФОП: {fop.name} (ЄДРПОУ: {fop.edrpou})")
        return fop

    def get_by_id(self, fop_id: int) -> FOP | None:
        
        return (
            self.db.query(FOP)
            .options(joinedload(FOP.nearest_branch), joinedload(FOP.person))
            .filter(FOP.id == fop_id)
            .first()
        )

    def get_by_edrpou(self, edrpou: str) -> FOP | None:
        
        return self.db.query(FOP).filter(FOP.edrpou == edrpou).first()

    def get_all(self) -> list[FOP]:
        
        return (
            self.db.query(FOP)
            .options(joinedload(FOP.nearest_branch))
            .all()
        )

    def get_by_district(self, district: str) -> list[FOP]:
        
        return (
            self.db.query(FOP)
            .filter(FOP.district.ilike(f"%{district}%"))
            .options(joinedload(FOP.nearest_branch))
            .all()
        )

    def get_without_branch(self) -> list[FOP]:
        
        return (
            self.db.query(FOP)
            .filter(FOP.nearest_branch_id.is_(None))
            .all()
        )

    def update_nearest_branch(self, fop_id: int, branch_id: int) -> FOP | None:
        
        fop = self.db.query(FOP).filter(FOP.id == fop_id).first()
        if fop:
            fop.nearest_branch_id = branch_id
            self.db.flush()
            logger.debug(f"Оновлено відділення для ФОП {fop.name}: branch_id={branch_id}")
        return fop

    def update_coordinates(
        self, fop_id: int, latitude: float, longitude: float
    ) -> FOP | None:
        
        fop = self.db.query(FOP).filter(FOP.id == fop_id).first()
        if fop:
            fop.latitude = latitude
            fop.longitude = longitude
            self.db.flush()
        return fop

    def get_or_create(self, fop_data: FOPCreate) -> tuple[FOP, bool]:
        
        if fop_data.edrpou:
            existing = self.get_by_edrpou(fop_data.edrpou)
            if existing:
                return existing, False

        fop = self.create(fop_data)
        return fop, True

    def count(self) -> int:
        
        return self.db.query(FOP).count()
