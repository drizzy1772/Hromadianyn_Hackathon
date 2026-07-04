import logging
import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from app.schemas.branch import BranchCreate

logger = logging.getLogger(__name__)

class UkrsibParseError(Exception):
    
    pass

class UkrsibBranchParser:

    BASE_URL = "https://my.ukrsibbank.com/ua/personal/branch/"

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
    }

    REGIONS = [
        "Вінницька", "Волинська", "Дніпропетровська", "Донецька",
        "Житомирська", "Закарпатська", "Запорізька", "Івано-Франківська",
        "Київська", "Кіровоградська", "Луганська", "Львівська",
        "Миколаївська", "Одеська", "Полтавська", "Рівненська",
        "Сумська", "Тернопільська", "Харківська", "Херсонська",
        "Хмельницька", "Черкаська", "Чернівецька", "Чернігівська",
    ]

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch_page(self, url: str | None = None) -> str:
        
        target_url = url or self.BASE_URL
        try:
            response = self.session.get(target_url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as e:
            raise UkrsibParseError(
                f"Не вдалося завантажити сторінку відділень UKRSIB: {e}"
            )

    def _extract_city_from_address(self, address: str) -> str | None:
        
        city_match = re.search(
            r"(?:м\.\s*|м\s+|місто\s+)([А-ЯІЇЄҐа-яіїєґ'\-]+)",
            address,
        )
        if city_match:
            return city_match.group(1).strip()

        parts = address.split(",")
        if parts:
            first_part = parts[0].strip()
            if not any(
                keyword in first_part.lower()
                for keyword in ["обл", "район", "р-н", "вул", "пр.", "просп"]
            ):
                return first_part

        return None

    def _extract_region_from_address(self, address: str) -> str | None:
        
        address_lower = address.lower()
        for region in self.REGIONS:
            if region.lower() in address_lower:
                return f"{region} обл."
        if "київ" in address_lower and "київська" not in address_lower:
            return "м. Київ"
        return None

    def _extract_district_from_address(self, address: str) -> str | None:
        
        district_match = re.search(
            r"([А-ЯІЇЄҐа-яіїєґ'\-]+)\s+(?:район|р-н|р\.)",
            address,
        )
        if district_match:
            return district_match.group(1).strip()
        return None

    def _parse_branch_element(self, element: Any) -> dict[str, Any] | None:
        
        branch_data = {}

        name_el = (
            element.find(class_=re.compile(r"branch.*name", re.I))
            or element.find("h3")
            or element.find("h4")
            or element.find(class_=re.compile(r"title", re.I))
        )
        if name_el:
            branch_data["name"] = name_el.get_text(strip=True)
        else:
            return None

        address_el = (
            element.find(class_=re.compile(r"address", re.I))
            or element.find("address")
            or element.find(class_=re.compile(r"location", re.I))
        )
        if address_el:
            branch_data["address"] = address_el.get_text(strip=True)
        else:
            all_text = element.get_text(separator="\n", strip=True).split("\n")
            for line in all_text:
                if any(
                    kw in line.lower()
                    for kw in ["вул.", "просп.", "пр.", "бульв.", "пл."]
                ):
                    branch_data["address"] = line.strip()
                    break

        if "address" not in branch_data:
            branch_data["address"] = ""

        phone_el = element.find(class_=re.compile(r"phone", re.I))
        if phone_el:
            branch_data["phone"] = phone_el.get_text(strip=True)
        else:
            phone_match = re.search(
                r"[\+]?[0-9\s\-\(\)]{10,}",
                element.get_text(),
            )
            if phone_match:
                branch_data["phone"] = phone_match.group().strip()

        schedule_el = element.find(
            class_=re.compile(r"schedule|hours|time|work", re.I)
        )
        if schedule_el:
            branch_data["working_hours"] = schedule_el.get_text(strip=True)

        lat = element.get("data-lat") or element.get("data-latitude")
        lon = element.get("data-lng") or element.get("data-longitude") or element.get("data-lon")
        if lat and lon:
            try:
                branch_data["latitude"] = float(lat)
                branch_data["longitude"] = float(lon)
            except (ValueError, TypeError):
                pass

        address = branch_data.get("address", "")
        if address:
            branch_data["city"] = self._extract_city_from_address(address)
            branch_data["region"] = self._extract_region_from_address(address)
            branch_data["district"] = self._extract_district_from_address(address)

        return branch_data

    def parse_branches(self, url: str | None = None) -> list[BranchCreate]:
        
        html = self.fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        branch_selectors = [
            {"class_": re.compile(r"branch", re.I)},
            {"class_": re.compile(r"office", re.I)},
            {"class_": re.compile(r"department", re.I)},
            {"class_": re.compile(r"item", re.I)},
        ]

        branch_elements = []
        for selector in branch_selectors:
            elements = soup.find_all("div", **selector)
            if elements:
                branch_elements = elements
                logger.info(
                    f"Знайдено {len(elements)} елементів за селектором {selector}"
                )
                break

        if not branch_elements:
            branch_elements = soup.find_all("li", class_=re.compile(r"branch|office", re.I))

        if not branch_elements:
            logger.warning(
                "Не вдалося знайти елементи відділень автоматично. "
                "Спробуємо парсити всі блоки з адресами."
            )
            branch_elements = soup.find_all(
                "div",
                string=re.compile(r"вул\.|просп\.|пр\.|бульв\.", re.I),
            )

        branches = []
        for element in branch_elements:
            branch_data = self._parse_branch_element(element)
            if branch_data and branch_data.get("name"):
                try:
                    branch = BranchCreate(**branch_data)
                    branches.append(branch)
                except Exception as e:
                    logger.warning(
                        f"Пропущено відділення через помилку валідації: {e}"
                    )

        logger.info(f"Спарсено {len(branches)} відділень UKRSIB Bank")
        return branches

    def parse_branches_from_json_api(self, url: str | None = None) -> list[BranchCreate]:
        
        target_url = url or f"{self.BASE_URL}api/branches/"
        try:
            response = self.session.get(target_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning(f"Сайт банку недоступний ({e}). Завантажуємо локальний список відділень...")
            import json
            import os
            try:
                path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "ukrsib_branches.json")
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as ex:
                logger.error(f"Не вдалося завантажити локальний файл: {ex}")
                return []

        branches = []
        items = data if isinstance(data, list) else data.get("data", data.get("items", []))

        for item in items:
            try:
                branch = BranchCreate(
                    name=item.get("name", item.get("title", "")),
                    address=item.get("address", ""),
                    city=item.get("city", ""),
                    region=item.get("region", ""),
                    district=item.get("district", ""),
                    latitude=item.get("lat", item.get("latitude")),
                    longitude=item.get("lng", item.get("longitude", item.get("lon"))),
                    phone=item.get("phone", ""),
                    working_hours=item.get("schedule", item.get("working_hours", "")),
                    branch_type=item.get("type", "відділення"),
                )
                branches.append(branch)
            except Exception as e:
                logger.warning(f"Пропущено відділення: {e}")

        logger.info(f"Спарсено {len(branches)} відділень з JSON API")
        return branches
