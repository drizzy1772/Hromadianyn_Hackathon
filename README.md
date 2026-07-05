# Project Description

Many newly registered sole proprietors (FOPs) need to submit documents or visit a bank branch during the onboarding process. However, registration data is often scattered across different sources, and manually searching for the nearest bank branch is time-consuming.

This project automates the entire workflow by collecting FOP registration data from multiple sources, validating and processing it, enriching addresses with geographic coordinates, and automatically finding the nearest **UKRSIB Bank** branch for each registered entrepreneur.

The application combines information from **vkursi.pro** and JSON datasets into a unified PostgreSQL database, making the data easy to search, analyze, and integrate into other systems.

The project demonstrates how web scraping, data validation, geocoding, spatial calculations, and database technologies can be combined into a single automated data-processing pipeline.

## Main Workflow

1. Parse FOP registration data from **vkursi.pro**.
2. Load and validate additional records from a JSON file.
3. Extract and normalize registration information.
4. Geocode business addresses using Nominatim.
5. Parse all available UKRSIB Bank branches.
6. Calculate the nearest branch for every registered FOP using the Haversine formula.
7. Store all processed and linked data in PostgreSQL.

## Problem Solved

* Eliminates manual processing of registration data.
* Automatically matches entrepreneurs with the nearest bank branch.
* Centralizes information from multiple sources into one database.
* Reduces repetitive work and minimizes human errors.
* Provides structured data that can be used for further analytics or business automation.


## Stack

- Python 3.11+
- PostgreSQL
- SQLAlchemy 2.0
- Pydantic 2.0
- BeautifulSoup4
- geopy (Nominatim)
- Alembic

## Key Features

- ✅ Parse FOP registration data from **vkursi.pro**
- ✅ Load and validate FOP records from JSON
- ✅ Parse UKRSIB Bank branch locations
- ✅ Geocode addresses using Nominatim
- ✅ Find the nearest UKRSIB branch using the Haversine formula
- ✅ Store processed data in PostgreSQL with SQLAlchemy ORM
- ✅ Database migrations with Alembic
- ✅ Modular architecture with repositories and services

## Project Structure

```text
Hromadianyn_F/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db/
│   ├── repositories/
│   ├── schemas/
│   └── services/
├── data/
├── tests/
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Database Tables

| Table | Description |
|-------|-------------|
| physical_persons | Personal information |
| fops | Sole proprietors linked to individuals and bank branches |
| legal_entities | Companies and legal entities |
| ukrsib_branches | UKRSIB Bank branches with coordinates |
| vkursi_records | Raw records parsed from vkursi.pro |

## Quick Start

```bash
# Clone repository
git clone https://github.com/username/Hromadianyn_F.git

cd Hromadianyn_F

# Create virtual environment
python -m venv venv

# Activate environment (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Create PostgreSQL database
createdb hromadianyn_db
```

## Run

```bash
# Full pipeline
python -m app.main --vkursi-url "https://vkursi.pro/your-url" --fop-file data/fop_registered.json

# JSON only
python -m app.main --fop-file data/fop_registered.json

# vkursi.pro only
python -m app.main --vkursi-url "https://vkursi.pro/your-url"

# Verbose mode
python -m app.main --fop-file data/fop_registered.json --verbose
```

## Authors

This project was developed during an **AI/Machine Learning Hackathon** by a team of four developers, including **Drizzy1772**.
