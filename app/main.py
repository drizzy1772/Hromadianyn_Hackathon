import argparse
import logging
import sys
from datetime import datetime

from app.config import settings
from app.db.database import Base, SessionLocal, engine
from app.db.models import FOP, LegalEntity, UkrsibBranch, VkursiRecord
from app.repositories.branch_repo import BranchRepository
from app.repositories.company_repo import CompanyRepository
from app.repositories.fop_repo import FOPRepository
from app.repositories.person_repo import PersonRepository
from app.schemas.branch import BranchCreate
from app.schemas.company import CompanyCreate
from app.schemas.fop import FOPCreate
from app.schemas.person import PersonCreate
from app.services.address_filter import parse_address
from app.services.branch_finder import BranchFinder
from app.services.fop_file_loader import FOPFileLoader
from app.services.geocoder import Geocoder
from app.services.ukrsib_parser import UkrsibBranchParser
from app.services.vkursi_parser import VkursiParser

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

def create_tables():
    
    logger.info("Створення таблиць в БД...")
    Base.metadata.create_all(bind=engine)
    logger.info("Таблиці створено успішно")

def step1_load_branches(db_session) -> list[UkrsibBranch]:
    
    logger.info("=" * 60)
    logger.info("КРОК 1: Завантаження відділень UKRSIB Bank")
    logger.info("=" * 60)

    branch_repo = BranchRepository(db_session)

    existing_count = branch_repo.count()
    if existing_count > 0:
        logger.info(
            f"В БД вже є {existing_count} відділень UKRSIB. Пропускаємо парсинг."
        )
        return branch_repo.get_all()

    parser = UkrsibBranchParser()
    try:
        branches_data = parser.parse_branches()
    except Exception as e:
        logger.error(f"Помилка парсингу відділень UKRSIB: {e}")
        logger.info("Спробуємо JSON API...")
        try:
            branches_data = parser.parse_branches_from_json_api()
        except Exception as e2:
            logger.error(f"JSON API також недоступний: {e2}")
            branches_data = []

    if not branches_data:
        logger.warning("Не вдалося отримати відділення UKRSIB. Продовжуємо без них.")
        return []

    geocoder = Geocoder()
    for branch_data in branches_data:
        if branch_data.latitude is None or branch_data.longitude is None:
            coords = geocoder.geocode(branch_data.address)
            if coords:
                branch_data.latitude = coords[0]
                branch_data.longitude = coords[1]

    branches = branch_repo.bulk_create(branches_data)
    db_session.commit()

    logger.info(f"Збережено {len(branches)} відділень UKRSIB Bank")
    return branches

def step2_parse_vkursi(db_session, vkursi_url: str) -> list[VkursiRecord]:
    
    logger.info("=" * 60)
    logger.info("КРОК 2: Парсинг таблиці з vkursi.pro")
    logger.info("=" * 60)

    if not vkursi_url:
        logger.warning("URL vkursi.pro не вказано. Пропускаємо крок.")
        return []

    parser = VkursiParser()
    try:
        records_data = parser.parse_table_to_schema(vkursi_url)
    except Exception as e:
        logger.error(f"Помилка парсингу vkursi.pro: {e}")
        return []

    if not records_data:
        logger.warning("Таблиця vkursi.pro порожня")
        return []

    vkursi_records = []
    for record_data in records_data:
        record = VkursiRecord(**record_data)
        db_session.add(record)
        vkursi_records.append(record)

    db_session.flush()
    db_session.commit()

    logger.info(f"Збережено {len(vkursi_records)} записів з vkursi.pro")
    return vkursi_records

def step3_load_fop_file(fop_file_path: str):
    
    logger.info("=" * 60)
    logger.info("КРОК 3: Завантаження JSON-файлу з ФОП")
    logger.info("=" * 60)

    if not fop_file_path:
        logger.warning("Шлях до JSON-файлу не вказано. Пропускаємо крок.")
        return []

    loader = FOPFileLoader()
    try:
        fops = loader.load(fop_file_path)
    except Exception as e:
        logger.error(f"Помилка завантаження файлу ФОП: {e}")
        return []

    logger.info(f"Завантажено {len(fops)} ФОП з файлу")
    return fops

def step4_process_and_save(
    db_session,
    fop_list,
    vkursi_records: list[VkursiRecord],
    branches: list[UkrsibBranch],
):
    
    logger.info("=" * 60)
    logger.info("КРОК 4: Обробка та збереження записів")
    logger.info("=" * 60)

    person_repo = PersonRepository(db_session)
    fop_repo = FOPRepository(db_session)
    company_repo = CompanyRepository(db_session)

    geocoder = Geocoder()
    branch_finder = BranchFinder(branches)

    stats = {
        "fops_created": 0,
        "fops_skipped": 0,
        "companies_created": 0,
        "companies_skipped": 0,
        "persons_created": 0,
        "geocoded": 0,
        "branches_assigned": 0,
    }

    total_fops = len(fop_list)
    for idx, fop_data in enumerate(fop_list, 1):
        if idx % 50 == 0:
            logger.info(f"Обробка ФОП: {idx}/{total_fops}")

        address_info = parse_address(fop_data.address)

        person_schema = PersonCreate(
            first_name=fop_data.first_name,
            last_name=fop_data.last_name,
            middle_name=fop_data.middle_name,
            inn=fop_data.edrpou, 
            address=fop_data.address,
            district=address_info["district"],
            region=address_info["region"],
            city=address_info["city"],
        )
        person, person_created = person_repo.get_or_create(person_schema)
        if person_created:
            stats["persons_created"] += 1

        latitude, longitude = None, None
        coords = geocoder.geocode(fop_data.address)
        if coords:
            latitude, longitude = coords
            stats["geocoded"] += 1

        nearest_branch_id = None
        if latitude and longitude and branches:
            nearest_branch, distance = branch_finder.find_nearest(latitude, longitude)
            if nearest_branch:
                nearest_branch_id = nearest_branch.id
                stats["branches_assigned"] += 1

        fop_schema = FOPCreate(
            person_id=person.id,
            edrpou=fop_data.edrpou,
            name=fop_data.name,
            registration_date=fop_data.registration_date,
            activity_type=fop_data.activity_type,
            address=fop_data.address,
            district=address_info["district"],
            region=address_info["region"],
            latitude=latitude,
            longitude=longitude,
            nearest_branch_id=nearest_branch_id,
        )
        fop, created = fop_repo.get_or_create(fop_schema)
        if created:
            stats["fops_created"] += 1
        else:
            stats["fops_skipped"] += 1

    for record in vkursi_records:
        if record.processed:
            continue

        address = record.address or ""
        address_info = parse_address(address)

        latitude, longitude = None, None
        if address:
            coords = geocoder.geocode(address)
            if coords:
                latitude, longitude = coords
                stats["geocoded"] += 1

        nearest_branch_id = None
        if latitude and longitude and branches:
            nearest_branch, distance = branch_finder.find_nearest(latitude, longitude)
            if nearest_branch:
                nearest_branch_id = nearest_branch.id
                stats["branches_assigned"] += 1

        if record.entity_type == "legal_entity":
            company_schema = CompanyCreate(
                edrpou=record.edrpou or "",
                name=record.name or "",
                address=address,
                district=address_info["district"],
                region=address_info["region"],
                registration_date=None, 
                activity_type=record.activity_type,
                latitude=latitude,
                longitude=longitude,
                nearest_branch_id=nearest_branch_id,
            )
            company, created = company_repo.get_or_create(company_schema)
            if created:
                stats["companies_created"] += 1
            else:
                stats["companies_skipped"] += 1
        else:
            first_name = record.first_name or ""
            last_name = record.last_name or ""

            person_schema = PersonCreate(
                first_name=first_name,
                last_name=last_name,
                inn=record.edrpou,
                address=address,
                district=address_info["district"],
                region=address_info["region"],
                city=address_info["city"],
            )
            person, person_created = person_repo.get_or_create(person_schema)
            if person_created:
                stats["persons_created"] += 1

            fop_schema = FOPCreate(
                person_id=person.id,
                edrpou=record.edrpou,
                name=record.name or f"ФОП {last_name} {first_name}",
                registration_date=None, 
                activity_type=record.activity_type,
                address=address,
                district=address_info["district"],
                region=address_info["region"],
                latitude=latitude,
                longitude=longitude,
                nearest_branch_id=nearest_branch_id,
            )
            fop, created = fop_repo.get_or_create(fop_schema)
            if created:
                stats["fops_created"] += 1
            else:
                stats["fops_skipped"] += 1

        record.processed = True

    db_session.commit()
    return stats

def print_summary(stats: dict):
    
    logger.info("=" * 60)
    logger.info("РЕЗУЛЬТАТИ ОБРОБКИ")
    logger.info("=" * 60)
    logger.info(f"  Фізичних осіб створено:    {stats.get('persons_created', 0)}")
    logger.info(f"  ФОП створено:              {stats.get('fops_created', 0)}")
    logger.info(f"  ФОП пропущено (дублі):     {stats.get('fops_skipped', 0)}")
    logger.info(f"  Юр. осіб створено:         {stats.get('companies_created', 0)}")
    logger.info(f"  Юр. осіб пропущено:        {stats.get('companies_skipped', 0)}")
    logger.info(f"  Адрес геокодовано:          {stats.get('geocoded', 0)}")
    logger.info(f"  Відділень призначено:       {stats.get('branches_assigned', 0)}")
    logger.info("=" * 60)

def run_pipeline(
    vkursi_url: str | None = None,
    fop_file_path: str | None = None,
):
    
    start_time = datetime.now()
    logger.info(f"Початок обробки: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    create_tables()

    db_session = SessionLocal()

    try:
        branches = step1_load_branches(db_session)

        vkursi_records = step2_parse_vkursi(
            db_session, vkursi_url or settings.vkursi_url
        )

        fop_list = step3_load_fop_file(fop_file_path) if fop_file_path else []

        stats = step4_process_and_save(
            db_session, fop_list, vkursi_records, branches
        )

        print_summary(stats)

    except Exception as e:
        logger.error(f"Критична помилка: {e}", exc_info=True)
        db_session.rollback()
        raise
    finally:
        db_session.close()

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Обробка завершена за {duration}")

def main():
    
    parser = argparse.ArgumentParser(
        description="Обробка даних ФОП з vkursi.pro та пошук відділень UKRSIB Bank",
    )
    parser.add_argument(
        "--vkursi-url",
        type=str,
        default=None,
        help="URL таблиці на vkursi.pro",
    )
    parser.add_argument(
        "--fop-file",
        type=str,
        default=None,
        help="Шлях до JSON-файлу з зареєстрованими ФОП",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Детальне логування (DEBUG рівень)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.vkursi_url and not args.fop_file:
        logger.warning(
            "Не вказано жодного джерела даних. "
            "Використовуйте --vkursi-url та/або --fop-file"
        )
        parser.print_help()
        sys.exit(1)

    run_pipeline(
        vkursi_url=args.vkursi_url,
        fop_file_path=args.fop_file,
    )

if __name__ == "__main__":
    main()
