import json
import logging
from pathlib import Path

from pydantic import ValidationError

from app.schemas.fop import FOPFromJSON

logger = logging.getLogger(__name__)

class FOPFileLoadError(Exception):
    
    pass

class FOPFileLoader:

    def load(self, file_path: str) -> list[FOPFromJSON]:
        
        path = Path(file_path)

        if not path.exists():
            raise FOPFileLoadError(f"Файл не знайдено: {file_path}")

        if not path.suffix.lower() == ".json":
            raise FOPFileLoadError(
                f"Очікується JSON-файл, отримано: {path.suffix}"
            )

        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise FOPFileLoadError(f"Невалідний JSON у файлі {file_path}: {e}")
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="cp1251") as f:
                    raw_data = json.load(f)
            except Exception as e:
                raise FOPFileLoadError(
                    f"Не вдалося прочитати файл {file_path}: {e}"
                )

        if isinstance(raw_data, dict):
            items = raw_data.get("data", raw_data.get("items", raw_data.get("results", [])))
        elif isinstance(raw_data, list):
            items = raw_data
        else:
            raise FOPFileLoadError(
                f"Невірна структура JSON: очікується масив або об'єкт з полем 'data'"
            )

        fops: list[FOPFromJSON] = []
        errors: list[str] = []

        for idx, item in enumerate(items):
            try:
                fop = FOPFromJSON.model_validate(item)
                fops.append(fop)
            except ValidationError as e:
                error_msg = f"Рядок {idx + 1}: {e}"
                errors.append(error_msg)
                logger.warning(f"Пропущено запис {item}")

        if errors:
            logger.warning(
                f"Під час завантаження пропущено {len(errors)} записів з {len(items)}"
            )

        logger.info(
            f"Завантажено {len(fops)} ФОП з файлу {file_path} "
            f"(всього записів: {len(items)}, помилок: {len(errors)})"
        )

        return fops

    def load_raw(self, file_path: str) -> list[dict]:
        
        path = Path(file_path)

        if not path.exists():
            raise FOPFileLoadError(f"Файл не знайдено: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if isinstance(raw_data, dict):
            return raw_data.get("data", raw_data.get("items", []))
        elif isinstance(raw_data, list):
            return raw_data

        return []
