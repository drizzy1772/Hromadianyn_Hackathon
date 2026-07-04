import logging
import re

logger = logging.getLogger(__name__)

REGIONS_MAP: dict[str, str] = {
    "вінницьк": "Вінницька",
    "волинськ": "Волинська",
    "дніпропетровськ": "Дніпропетровська",
    "донецьк": "Донецька",
    "житомирськ": "Житомирська",
    "закарпатськ": "Закарпатська",
    "запорізьк": "Запорізька",
    "івано-франківськ": "Івано-Франківська",
    "київськ": "Київська",
    "кіровоградськ": "Кіровоградська",
    "луганськ": "Луганська",
    "львівськ": "Львівська",
    "миколаївськ": "Миколаївська",
    "одеськ": "Одеська",
    "полтавськ": "Полтавська",
    "рівненськ": "Рівненська",
    "сумськ": "Сумська",
    "тернопільськ": "Тернопільська",
    "харківськ": "Харківська",
    "херсонськ": "Херсонська",
    "хмельницьк": "Хмельницька",
    "черкаськ": "Черкаська",
    "чернівецьк": "Чернівецька",
    "чернігівськ": "Чернігівська",
}

def extract_district(address: str) -> str | None:
    
    if not address:
        return None

    match = re.search(
        r"([А-ЯІЇЄҐа-яіїєґ'\-]+)\s+"
        r"(?:район|р-н|р\.)",
        address,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()

    match = re.search(
        r"(?:район|р-н|р\.)\s+([А-ЯІЇЄҐа-яіїєґ'\-]+)",
        address,
        re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()

    return None

def extract_region(address: str) -> str | None:
    
    if not address:
        return None

    address_lower = address.lower()

    if re.search(r"м\.\s*київ(?!\s*обл)", address_lower):
        return "м. Київ"

    for key, region_name in REGIONS_MAP.items():
        if key in address_lower:
            return f"{region_name} обл."

    return None

def extract_city(address: str) -> str | None:
    
    if not address:
        return None

    match = re.search(
        r"(?:м\.\s*|м\s+|місто\s+)([А-ЯІЇЄҐа-яіїєґ'\-]+)",
        address,
    )
    if match:
        return match.group(1).strip()

    match = re.search(
        r"(?:смт\.\s*|смт\s+)([А-ЯІЇЄҐа-яіїєґ'\-]+)",
        address,
    )
    if match:
        return match.group(1).strip()

    return None

def is_target_district(address: str, target_district: str) -> bool:
    
    district = extract_district(address)
    if not district:
        return False

    return district.lower().startswith(target_district.lower())

def parse_address(address: str) -> dict[str, str | None]:
    
    return {
        "district": extract_district(address),
        "region": extract_region(address),
        "city": extract_city(address),
    }
