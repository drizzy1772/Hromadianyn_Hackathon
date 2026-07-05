Hromadianyn FOP — FOP Data Processing

A collaborative hackathon project for automated processing of Ukrainian Sole Proprietor (FOP) registration data. Developed by a team of four during an AI/Machine Learning hackathon. The application parses registration information, processes addresses, finds the nearest UKRSIB Bank branch, and stores the data in PostgreSQL.

Stack
Python 3.11+
PostgreSQL
SQLAlchemy 2.0
Pydantic 2.0
BeautifulSoup4
geopy (Nominatim)
Alembic
Key Features
✅ Parse FOP registration data from vkursi.pro
✅ Load and validate FOP records from JSON
✅ Parse UKRSIB Bank branch locations
✅ Geocode addresses using Nominatim
✅ Find the nearest UKRSIB branch using the Haversine formula
✅ Store processed data in PostgreSQL with SQLAlchemy ORM
✅ Database migrations with Alembic
✅ Modular architecture with repositories and services

## Project Structure
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
Database Tables
Table	Description
physical_persons	Personal information
fops	Sole proprietors linked to individuals and bank branches
legal_entities	Companies and legal entities
ukrsib_branches	UKRSIB Bank branches with coordinates
vkursi_records	Raw records parsed from vkursi.pro
Quick Start
# Clone repository
git clone https://github.com/username/Hromadianyn_F.git

cd Hromadianyn_F

# Create virtual environment
python -m venv venv

# Activate environment
source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Create PostgreSQL database
createdb hromadianyn_db
Run
# Full pipeline
python -m app.main --vkursi-url "https://vkursi.pro/your-url" --fop-file data/fop_registered.json

# JSON only
python -m app.main --fop-file data/fop_registered.json

# vkursi.pro only
python -m app.main --vkursi-url "https://vkursi.pro/your-url"

# Verbose mode
python -m app.main --fop-file data/fop_registered.json --verbose
Authors

This project was developed during an AI/Machine Learning Hackathon by a team of four developers, including Drizzy1772.
