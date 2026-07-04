import logging

from sqlalchemy.orm import Session

from app.db.models import UkrsibBranch
from app.schemas.branch import BranchCreate

logger = logging.getLogger(__name__)

class BranchRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, branch_data: BranchCreate) -> UkrsibBranch:
        
        branch = UkrsibBranch(**branch_data.model_dump())
        self.db.add(branch)
        self.db.flush()
        logger.debug(f"Створено відділення: {branch.name}")
        return branch

    def bulk_create(self, branches_data: list[BranchCreate]) -> list[UkrsibBranch]:
        
        branches = [UkrsibBranch(**data.model_dump()) for data in branches_data]
        self.db.add_all(branches)
        self.db.flush()
        logger.info(f"Створено {len(branches)} відділень")
        return branches

    def get_by_id(self, branch_id: int) -> UkrsibBranch | None:
        
        return self.db.query(UkrsibBranch).filter(UkrsibBranch.id == branch_id).first()

    def get_all(self) -> list[UkrsibBranch]:
        
        return self.db.query(UkrsibBranch).all()

    def get_by_city(self, city: str) -> list[UkrsibBranch]:
        
        return (
            self.db.query(UkrsibBranch)
            .filter(UkrsibBranch.city.ilike(f"%{city}%"))
            .all()
        )

    def get_by_region(self, region: str) -> list[UkrsibBranch]:
        
        return (
            self.db.query(UkrsibBranch)
            .filter(UkrsibBranch.region.ilike(f"%{region}%"))
            .all()
        )

    def get_with_coordinates(self) -> list[UkrsibBranch]:
        
        return (
            self.db.query(UkrsibBranch)
            .filter(
                UkrsibBranch.latitude.isnot(None),
                UkrsibBranch.longitude.isnot(None),
            )
            .all()
        )

    def count(self) -> int:
        
        return self.db.query(UkrsibBranch).count()

    def delete_all(self) -> int:
        
        count = self.db.query(UkrsibBranch).delete()
        self.db.flush()
        logger.info(f"Видалено {count} відділень")
        return count
