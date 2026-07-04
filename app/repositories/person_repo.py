import logging

from sqlalchemy.orm import Session

from app.db.models import PhysicalPerson
from app.schemas.person import PersonCreate

logger = logging.getLogger(__name__)

class PersonRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, person_data: PersonCreate) -> PhysicalPerson:
        
        person = PhysicalPerson(**person_data.model_dump())
        self.db.add(person)
        self.db.flush()
        logger.debug(f"Створено фіз. особу: {person.last_name} {person.first_name}")
        return person

    def get_by_id(self, person_id: int) -> PhysicalPerson | None:
        
        return (
            self.db.query(PhysicalPerson)
            .filter(PhysicalPerson.id == person_id)
            .first()
        )

    def get_by_inn(self, inn: str) -> PhysicalPerson | None:
        
        return (
            self.db.query(PhysicalPerson)
            .filter(PhysicalPerson.inn == inn)
            .first()
        )

    def get_by_name(self, first_name: str, last_name: str) -> PhysicalPerson | None:
        
        return (
            self.db.query(PhysicalPerson)
            .filter(
                PhysicalPerson.first_name.ilike(first_name),
                PhysicalPerson.last_name.ilike(last_name),
            )
            .first()
        )

    def get_all(self) -> list[PhysicalPerson]:
        
        return self.db.query(PhysicalPerson).all()

    def get_by_district(self, district: str) -> list[PhysicalPerson]:
        
        return (
            self.db.query(PhysicalPerson)
            .filter(PhysicalPerson.district.ilike(f"%{district}%"))
            .all()
        )

    def get_or_create(self, person_data: PersonCreate) -> tuple[PhysicalPerson, bool]:
        
        if person_data.inn:
            existing = self.get_by_inn(person_data.inn)
            if existing:
                return existing, False

        existing = self.get_by_name(person_data.first_name, person_data.last_name)
        if existing:
            return existing, False

        person = self.create(person_data)
        return person, True

    def count(self) -> int:
        
        return self.db.query(PhysicalPerson).count()
