import logging
from typing import Any

import requests
from bs4 import BeautifulSoup, Tag
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class VkursiParseError(Exception):
    
    pass

class VkursiParser:

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
    }

    COLUMN_MAPPING = {
        "єдрпоу": "edrpou",
        "код єдрпоу": "edrpou",
        "код": "edrpou",
        "назва": "name",
        "найменування": "name",
        "адреса": "address",
        "адреса реєстрації": "address",
        "місцезнаходження": "address",
        "дата реєстрації": "registration_date",
        "дата": "registration_date",
        "ім'я": "first_name",
        "імя": "first_name",
        "прізвище": "last_name",
        "вид діяльності": "activity_type",
        "квед": "activity_type",
        "основний вид діяльності": "activity_type",
    }

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch_page(self, url: str) -> str:
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as e:
            raise VkursiParseError(f"Не вдалося завантажити сторінку {url}: {e}")

    def _normalize_header(self, header: str) -> str | None:
        
        header_lower = header.strip().lower()
        return self.COLUMN_MAPPING.get(header_lower)

    def _extract_table_headers(self, table: Tag) -> list[str | None]:
        
        headers = []
        header_row = table.find("thead")
        if header_row:
            ths = header_row.find_all("th")
        else:
            first_row = table.find("tr")
            ths = first_row.find_all(["th", "td"]) if first_row else []

        for th in ths:
            text = th.get_text(strip=True)
            field_name = self._normalize_header(text)
            headers.append(field_name)
            if field_name:
                logger.debug(f"Колонка '{text}' → поле '{field_name}'")
            else:
                logger.debug(f"Колонка '{text}' → пропущено")

        return headers

    def _extract_full_name(self, name_text: str) -> dict[str, str]:
        
        parts = name_text.strip().split()
        result = {}

        if len(parts) >= 2:
            result["last_name"] = parts[0]
            result["first_name"] = parts[1]
        elif len(parts) == 1:
            result["last_name"] = parts[0]
            result["first_name"] = ""
        else:
            result["last_name"] = ""
            result["first_name"] = ""

        return result

    def _parse_row(self, row: Tag, headers: list[str | None]) -> dict[str, Any]:
        
        cells = row.find_all("td")
        record: dict[str, Any] = {}

        for idx, cell in enumerate(cells):
            if idx < len(headers) and headers[idx]:
                field_name = headers[idx]
                value = cell.get_text(strip=True)
                if value:
                    record[field_name] = value

        return record

    def _determine_entity_type(self, record: dict[str, Any]) -> str:
        
        name = record.get("name", "").upper()

        legal_prefixes = ["ТОВ ", "ПП ", "ПАТ ", "ПРАТ ", "ТДВ ", "КТ "]
        for prefix in legal_prefixes:
            if prefix in name or name.startswith(prefix):
                return "legal_entity"

        return "fop"

    def parse_table(self, url: str) -> list[dict[str, Any]]:
        
        html = self.fetch_page(url)
        soup = BeautifulSoup(html, "lxml")

        table = (
            soup.find("table", class_="table")
            or soup.find("table", {"id": True})
            or soup.find("table")
        )

        if not table:
            raise VkursiParseError(
                f"Таблиця не знайдена на сторінці {url}. "
                "Перевірте URL або структуру сторінки."
            )

        headers = self._extract_table_headers(table)

        if not any(headers):
            raise VkursiParseError(
                "Не вдалося розпізнати заголовки таблиці. "
                f"Знайдені заголовки: {headers}"
            )

        records = []
        tbody = table.find("tbody") or table
        rows = tbody.find_all("tr")

        for row in rows:
            if row.find("th"):
                continue

            record = self._parse_row(row, headers)

            if not record:
                continue

            record["entity_type"] = self._determine_entity_type(record)

            if "first_name" not in record and "name" in record:
                name = record["name"]
                if record["entity_type"] == "fop":
                    clean_name = name.replace("ФОП", "").replace("ФО-П", "").strip()
                    name_parts = self._extract_full_name(clean_name)
                    record.update(name_parts)

            records.append(record)

        logger.info(f"Спарсено {len(records)} записів з {url}")
        return records

    def parse_table_to_schema(self, url: str) -> list[dict[str, Any]]:
        
        raw_records = self.parse_table(url)
        result = []

        for record in raw_records:
            schema_record = {
                "source_url": url,
                "edrpou": record.get("edrpou"),
                "name": record.get("name"),
                "address": record.get("address"),
                "registration_date": record.get("registration_date"),
                "first_name": record.get("first_name"),
                "last_name": record.get("last_name"),
                "activity_type": record.get("activity_type"),
                "entity_type": record.get("entity_type", "fop"),
                "raw_data": record,
                "processed": False,
            }
            result.append(schema_record)

        return result
