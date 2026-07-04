cd "$(dirname "$0")"
source venv/bin/activate
uvicorn app.server:app --reload --port 8000

