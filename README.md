# Hromadianyn FOP — Обробка даних ФОП

Скрипт для автоматизованої обробки реєстраційних даних ФОП (фізичних осіб-підприємців) з інтеграцією vkursi.pro та пошуком найближчих відділень UKRSIB Bank.

## Можливості

- 🌐 **Парсинг vkursi.pro** — витягує дані з HTML-таблиці (ЄДРПОУ, назва, адреса, дата реєстрації, ім'я, прізвище, вид діяльності)
- 📄 **Завантаження JSON** — валідує та завантажує файл з зареєстрованими ФОП
- 🏦 **Парсинг UKRSIB Bank** — отримує список відділень з сайту банку
- 📍 **Геокодування** — перетворює адреси в координати (Nominatim, безкоштовно)
- 🗺️ **Пошук відділення** — знаходить найближче відділення UKRSIB (Haversine formula)
- 🗄️ **PostgreSQL** — зберігає дані через SQLAlchemy ORM

## Технології

| Технологія | Призначення |
|------------|-------------|
| Python 3.11+ | Мова програмування |
| SQLAlchemy 2.0 | ORM для PostgreSQL |
| Pydantic 2.0 | Валідація даних |
| PostgreSQL | База даних |
| BeautifulSoup4 | Парсинг HTML |
| geopy (Nominatim) | Геокодування адрес |
| Alembic | Міграції БД |

## Встановлення

```bash
# 1. Клонуємо репозиторій
cd Hromadianyn_F

# 2. Створюємо віртуальне середовище
python -m venv venv
source venv/bin/activate  # macOS/Linux

# 3. Встановлюємо залежності
pip install -r requirements.txt

# 4. Копіюємо та налаштовуємо .env
cp .env.example .env
# Відредагуйте .env — вкажіть DATABASE_URL

# 5. Створюємо базу даних PostgreSQL
createdb hromadianyn_db
```

## Запуск

```bash
# Повний pipeline (vkursi.pro + JSON файл)
python -m app.main --vkursi-url "https://vkursi.pro/your-url" --fop-file data/fop_registered.json

# Тільки JSON файл
python -m app.main --fop-file data/fop_registered.json

# Тільки vkursi.pro
python -m app.main --vkursi-url "https://vkursi.pro/your-url"

# Детальне логування
python -m app.main --fop-file data/fop_registered.json --verbose
```

## Структура проєкту

```
Hromadianyn_F/
├── app/
│   ├── main.py                 # Головний pipeline
│   ├── config.py               # Конфігурація (Pydantic Settings)
│   ├── db/
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   └── models.py           # ORM-моделі (5 таблиць)
│   ├── schemas/                # Pydantic-схеми
│   │   ├── fop.py              # ФОП
│   │   ├── person.py           # Фізична особа
│   │   ├── company.py          # ТОВ / Юр. особа
│   │   └── branch.py           # Відділення банку
│   ├── services/               # Бізнес-логіка
│   │   ├── vkursi_parser.py    # Парсинг HTML з vkursi.pro
│   │   ├── ukrsib_parser.py    # Парсинг відділень UKRSIB
│   │   ├── fop_file_loader.py  # Завантаження JSON
│   │   ├── address_filter.py   # Визначення району/області
│   │   ├── geocoder.py         # Геокодування (Nominatim)
│   │   └── branch_finder.py    # Пошук найближчого відділення
│   └── repositories/           # CRUD-операції
│       ├── fop_repo.py
│       ├── person_repo.py
│       ├── company_repo.py
│       └── branch_repo.py
├── data/
│   └── fop_registered.json     # Приклад вхідного файлу
├── tests/
├── .env.example
├── requirements.txt
└── pyproject.toml
```

## База даних (таблиці)

| Таблиця | Опис |
|---------|------|
| `physical_persons` | Фізичні особи (ім'я, прізвище, ІПН, адреса) |
| `fops` | ФОП з прив'язкою до фіз. особи та відділення |
| `legal_entities` | Юридичні особи (ТОВ, ПП тощо) |
| `ukrsib_branches` | Відділення UKRSIB Bank з координатами |
| `vkursi_records` | Сирі записи з vkursi.pro |
