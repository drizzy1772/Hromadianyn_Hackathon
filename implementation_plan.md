# Система обробки ФОП з інтеграцією vkursi.pro та пошуком відділень UKRSIB Bank

## Опис

Скрипт для автоматизованої обробки реєстраційних даних ФОП:
1. Парсинг таблиці з сайту vkursi.pro
2. Завантаження файлу з зареєстрованими ФОП
3. Фільтрація за Шевченківським районом + пошук найближчого відділення UKRSIB Bank
4. Збереження в PostgreSQL (ФОП, фіз. особи, ТОВ, юр. особи, відділення банку)

## User Review Required

> [!IMPORTANT]
> **Формат вхідного файлу ФОП**: Який формат файлу з зареєстрованими ФОП? (CSV, Excel, JSON, XML?)

> [!IMPORTANT]
> **Доступ до vkursi.pro**: Чи є API-ключ або акаунт для vkursi.pro? Чи потрібен веб-скрапінг через Selenium/Playwright?

> [!WARNING]
> **Геокодування адрес**: Для пошуку найближчого відділення UKRSIB потрібен сервіс геокодування. Рекомендую OpenStreetMap Nominatim (безкоштовний) або Google Geocoding API (платний, але точніший). Який варіант обрати?

## Open Questions

1. **Авторизація vkursi.pro** — чи є у вас API-токен чи потрібно парсити HTML-сторінку?
2. **Джерело даних про відділення UKRSIB** — вручну задати список відділень чи парсити з сайту банку?
3. **Шевченківський район якого міста?** — Київ, чи інше місто?
4. **Які поля з таблиці vkursi.pro потрібні?** — ЄДРПОУ, назва, адреса, дата реєстрації, вид діяльності?
5. **Формат вхідного файлу ФОП** — CSV, XLSX, JSON?

## Proposed Changes

### Структура проєкту

```
Hromadianyn_F/
├── alembic/                    # Міграції БД
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                 # Точка входу
│   ├── config.py               # Конфігурація (DB URL, API keys)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy engine, session
│   │   └── models.py           # ORM-моделі (ФОП, ФізОсоба, ТОВ, ЮрОсоба, Відділення)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── fop.py              # Pydantic-схеми для ФОП
│   │   ├── person.py           # Pydantic-схеми для фіз. особи
│   │   ├── company.py          # Pydantic-схеми для ТОВ / Юр. особи
│   │   └── branch.py           # Pydantic-схеми для відділень банку
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vkursi_parser.py    # Парсинг таблиці з vkursi.pro
│   │   ├── fop_file_loader.py  # Завантаження файлу з ФОП
│   │   ├── address_filter.py   # Фільтрація за Шевченківським районом
│   │   ├── geocoder.py         # Геокодування адрес (координати)
│   │   └── branch_finder.py    # Пошук найближчого відділення UKRSIB
│   └── repositories/
│       ├── __init__.py
│       ├── fop_repo.py         # CRUD для ФОП
│       ├── person_repo.py      # CRUD для фіз. особи
│       ├── company_repo.py     # CRUD для ТОВ / Юр. особи
│       └── branch_repo.py      # CRUD для відділень банку
├── data/
│   └── ukrsib_branches.json    # Довідник відділень UKRSIB (статичний)
├── tests/
│   ├── __init__.py
│   ├── test_address_filter.py
│   ├── test_branch_finder.py
│   └── test_fop_loader.py
├── .env                        # Змінні середовища (DB_URL, API keys)
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

### Модуль БД — `app/db/`

#### [NEW] [database.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/db/database.py)
- SQLAlchemy async engine + sessionmaker
- Підключення до PostgreSQL через `asyncpg` або `psycopg2`
- Функція `get_db()` для dependency injection

#### [NEW] [models.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/db/models.py)
ORM-моделі:

```python
# Основні таблиці:
class PhysicalPerson(Base):     # Фізична особа
    id, full_name, inn, address, district, phone, email

class FOP(Base):                # ФОП
    id, person_id (FK), registration_number, registration_date,
    activity_type, status, address, nearest_branch_id (FK)

class LegalEntity(Base):       # Юридична особа (ТОВ, тощо)
    id, edrpou, name, legal_form, address, director_name,
    registration_date, nearest_branch_id (FK)

class UkrsibBranch(Base):      # Відділення UKRSIB Bank
    id, name, address, latitude, longitude, phone, working_hours

class VkursiRecord(Base):      # Запис з vkursi.pro
    id, source_url, entity_type, raw_data (JSONB), processed, created_at
```

---

### Pydantic-схеми — `app/schemas/`

#### [NEW] [fop.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/schemas/fop.py)
```python
class FOPCreate(BaseModel):
    full_name: str
    inn: str
    registration_number: str
    activity_type: str | None
    address: str
    district: str | None

class FOPResponse(FOPCreate):
    id: int
    nearest_branch: BranchResponse | None
```

#### [NEW] Аналогічні схеми для `person.py`, `company.py`, `branch.py`

---

### Сервіси — `app/services/`

#### [NEW] [vkursi_parser.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/services/vkursi_parser.py)
- Клас `VkursiParser` — парсинг HTML-таблиці з vkursi.pro
- Використовує `requests` + `BeautifulSoup` (або API, якщо доступний)
- Метод `parse_table(url: str) -> list[VkursiRecord]`

#### [NEW] [fop_file_loader.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/services/fop_file_loader.py)
- Клас `FOPFileLoader` — завантаження файлу з ФОП
- Підтримка CSV/XLSX/JSON
- Метод `load(file_path: str) -> list[FOPCreate]`

#### [NEW] [address_filter.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/services/address_filter.py)
- Функція `is_shevchenkivskyi_district(address: str) -> bool`
- Нормалізація адреси, пошук ключових слів ("Шевченківський район", "Шевченківський р-н")

#### [NEW] [geocoder.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/services/geocoder.py)
- Клас `Geocoder` — перетворення адреси в координати
- Використовує Nominatim (OpenStreetMap) через `geopy`
- Метод `geocode(address: str) -> tuple[float, float]`

#### [NEW] [branch_finder.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/services/branch_finder.py)
- Клас `BranchFinder` — пошук найближчого відділення
- Використовує Haversine formula для обчислення відстані
- Метод `find_nearest(lat: float, lon: float) -> UkrsibBranch`

---

### Конфігурація

#### [NEW] [config.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/config.py)
```python
class Settings(BaseSettings):
    database_url: str = "postgresql://user:pass@localhost:5432/hromadianyn"
    vkursi_api_key: str | None = None
    geocoder_provider: str = "nominatim"
    target_district: str = "Шевченківський"

    model_config = SettingsConfigDict(env_file=".env")
```

---

### Точка входу

#### [NEW] [main.py](file:///Users/drl-15/Desktop/Hromadianyn_F/app/main.py)
Основний pipeline:
```
1. Парсинг vkursi.pro → отримання списку записів
2. Завантаження файлу ФОП → список ФОП
3. Фільтрація за Шевченківським районом
4. Геокодування відфільтрованих адрес
5. Пошук найближчого відділення UKRSIB для кожного
6. Збереження всього в PostgreSQL
```

---

### Залежності

#### [NEW] [requirements.txt](file:///Users/drl-15/Desktop/Hromadianyn_F/requirements.txt)
```
sqlalchemy>=2.0
psycopg2-binary
pydantic>=2.0
pydantic-settings
requests
beautifulsoup4
lxml
geopy
openpyxl
python-dotenv
alembic
```

## Verification Plan

### Automated Tests
```bash
pytest tests/ -v
```

### Manual Verification
- Запуск міграцій: `alembic upgrade head`
- Тестове завантаження файлу ФОП
- Перевірка фільтрації за районом
- Перевірка підключення до PostgreSQL
- Тестовий запуск повного pipeline: `python -m app.main`
