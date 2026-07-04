from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.database import Base

class PhysicalPerson(Base):

    __tablename__ = "physical_persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(255), nullable=False, comment="Ім'я")
    last_name = Column(String(255), nullable=False, comment="Прізвище")
    middle_name = Column(String(255), nullable=True, comment="По-батькові")
    inn = Column(String(20), nullable=True, unique=True, comment="ІПН")
    address = Column(Text, nullable=True, comment="Адреса проживання")
    district = Column(String(255), nullable=True, comment="Район")
    region = Column(String(255), nullable=True, comment="Область")
    city = Column(String(255), nullable=True, comment="Місто")
    phone = Column(String(50), nullable=True, comment="Телефон")
    email = Column(String(255), nullable=True, comment="Email")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    fops = relationship("FOP", back_populates="person", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_physical_persons_inn", "inn"),
        Index("ix_physical_persons_district", "district"),
        Index("ix_physical_persons_last_name", "last_name"),
    )

    def __repr__(self):
        return f"<PhysicalPerson(id={self.id}, name='{self.last_name} {self.first_name}')>"

class FOP(Base):

    __tablename__ = "fops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(
        Integer,
        ForeignKey("physical_persons.id", ondelete="CASCADE"),
        nullable=False,
        comment="FK на фізичну особу",
    )
    edrpou = Column(String(20), nullable=True, unique=True, comment="ЄДРПОУ / ІПН")
    name = Column(String(500), nullable=False, comment="Назва ФОП")
    registration_date = Column(Date, nullable=True, comment="Дата реєстрації")
    activity_type = Column(Text, nullable=True, comment="Вид діяльності (КВЕД)")
    address = Column(Text, nullable=True, comment="Адреса реєстрації")
    district = Column(String(255), nullable=True, comment="Район")
    region = Column(String(255), nullable=True, comment="Область")
    status = Column(String(50), nullable=True, default="active", comment="Статус")
    latitude = Column(Float, nullable=True, comment="Широта")
    longitude = Column(Float, nullable=True, comment="Довгота")
    nearest_branch_id = Column(
        Integer,
        ForeignKey("ukrsib_branches.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK на найближче відділення UKRSIB",
    )
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    person = relationship("PhysicalPerson", back_populates="fops")
    nearest_branch = relationship("UkrsibBranch", back_populates="fops")

    __table_args__ = (
        Index("ix_fops_edrpou", "edrpou"),
        Index("ix_fops_district", "district"),
        Index("ix_fops_nearest_branch_id", "nearest_branch_id"),
    )

    def __repr__(self):
        return f"<FOP(id={self.id}, name='{self.name}', edrpou='{self.edrpou}')>"

class LegalEntity(Base):

    __tablename__ = "legal_entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    edrpou = Column(String(20), nullable=False, unique=True, comment="ЄДРПОУ")
    name = Column(String(500), nullable=False, comment="Назва")
    legal_form = Column(
        String(100), nullable=True, comment="Організаційно-правова форма (ТОВ, ПП тощо)"
    )
    address = Column(Text, nullable=True, comment="Юридична адреса")
    district = Column(String(255), nullable=True, comment="Район")
    region = Column(String(255), nullable=True, comment="Область")
    director_name = Column(String(500), nullable=True, comment="ПІБ директора")
    registration_date = Column(Date, nullable=True, comment="Дата реєстрації")
    activity_type = Column(Text, nullable=True, comment="Вид діяльності (КВЕД)")
    status = Column(String(50), nullable=True, default="active", comment="Статус")
    latitude = Column(Float, nullable=True, comment="Широта")
    longitude = Column(Float, nullable=True, comment="Довгота")
    nearest_branch_id = Column(
        Integer,
        ForeignKey("ukrsib_branches.id", ondelete="SET NULL"),
        nullable=True,
        comment="FK на найближче відділення UKRSIB",
    )
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    nearest_branch = relationship("UkrsibBranch", back_populates="legal_entities")

    __table_args__ = (
        Index("ix_legal_entities_edrpou", "edrpou"),
        Index("ix_legal_entities_district", "district"),
    )

    def __repr__(self):
        return f"<LegalEntity(id={self.id}, name='{self.name}', edrpou='{self.edrpou}')>"

class UkrsibBranch(Base):

    __tablename__ = "ukrsib_branches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(500), nullable=False, comment="Назва відділення")
    address = Column(Text, nullable=False, comment="Адреса")
    city = Column(String(255), nullable=True, comment="Місто")
    region = Column(String(255), nullable=True, comment="Область")
    district = Column(String(255), nullable=True, comment="Район")
    latitude = Column(Float, nullable=True, comment="Широта")
    longitude = Column(Float, nullable=True, comment="Довгота")
    phone = Column(String(100), nullable=True, comment="Телефон")
    working_hours = Column(Text, nullable=True, comment="Графік роботи")
    branch_type = Column(String(100), nullable=True, comment="Тип (відділення / банкомат)")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    fops = relationship("FOP", back_populates="nearest_branch")
    legal_entities = relationship("LegalEntity", back_populates="nearest_branch")

    __table_args__ = (
        Index("ix_ukrsib_branches_city", "city"),
        Index("ix_ukrsib_branches_region", "region"),
    )

    def __repr__(self):
        return f"<UkrsibBranch(id={self.id}, name='{self.name}', city='{self.city}')>"

class VkursiRecord(Base):

    __tablename__ = "vkursi_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(Text, nullable=False, comment="URL джерела")
    edrpou = Column(String(20), nullable=True, comment="ЄДРПОУ")
    name = Column(String(500), nullable=True, comment="Назва")
    address = Column(Text, nullable=True, comment="Адреса")
    registration_date = Column(String(50), nullable=True, comment="Дата реєстрації (сира)")
    first_name = Column(String(255), nullable=True, comment="Ім'я")
    last_name = Column(String(255), nullable=True, comment="Прізвище")
    activity_type = Column(Text, nullable=True, comment="Вид діяльності")
    entity_type = Column(
        String(50), nullable=False, default="fop",
        comment="Тип: fop / legal_entity",
    )
    raw_data = Column(JSONB, nullable=True, comment="Повні сирі дані")
    processed = Column(Boolean, default=False, comment="Чи оброблено")
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_vkursi_records_edrpou", "edrpou"),
        Index("ix_vkursi_records_processed", "processed"),
        Index("ix_vkursi_records_entity_type", "entity_type"),
    )

    def __repr__(self):
        return (
            f"<VkursiRecord(id={self.id}, edrpou='{self.edrpou}', "
            f"type='{self.entity_type}', processed={self.processed})>"
        )
