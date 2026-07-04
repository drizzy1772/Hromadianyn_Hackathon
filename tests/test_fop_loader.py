import json
import os
import tempfile

import pytest

from app.services.fop_file_loader import FOPFileLoadError, FOPFileLoader

class TestFOPFileLoader:
    def _create_temp_json(self, data, suffix=".json"):
        
        tmp = tempfile.NamedTemporaryFile(
            mode="w",
            suffix=suffix,
            delete=False,
            encoding="utf-8",
        )
        json.dump(data, tmp, ensure_ascii=False)
        tmp.close()
        return tmp.name

    def test_load_valid_json(self):
        
        data = [
            {
                "edrpou": "1234567890",
                "name": "ФОП Іванов Іван",
                "first_name": "Іван",
                "last_name": "Іванов",
                "address": "м. Київ, вул. Хрещатик, 1",
                "registration_date": "2024-01-15",
                "activity_type": "47.11",
            }
        ]
        path = self._create_temp_json(data)
        try:
            loader = FOPFileLoader()
            result = loader.load(path)
            assert len(result) == 1
            assert result[0].edrpou == "1234567890"
            assert result[0].first_name == "Іван"
            assert result[0].last_name == "Іванов"
        finally:
            os.unlink(path)

    def test_load_with_data_wrapper(self):
        
        data = {
            "data": [
                {
                    "edrpou": "9999999999",
                    "name": "ФОП Тестовий",
                    "first_name": "Тест",
                    "last_name": "Тестовий",
                    "address": "м. Львів",
                }
            ]
        }
        path = self._create_temp_json(data)
        try:
            loader = FOPFileLoader()
            result = loader.load(path)
            assert len(result) == 1
        finally:
            os.unlink(path)

    def test_load_partial_errors(self):
        
        data = [
            {
                "edrpou": "1111111111",
                "name": "ФОП Валідний",
                "first_name": "Валід",
                "last_name": "Валідний",
                "address": "м. Київ",
            },
            {
                "some_field": "value",
            },
        ]
        path = self._create_temp_json(data)
        try:
            loader = FOPFileLoader()
            result = loader.load(path)
            assert len(result) == 1
            assert result[0].edrpou == "1111111111"
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        
        loader = FOPFileLoader()
        with pytest.raises(FOPFileLoadError, match="Файл не знайдено"):
            loader.load("/nonexistent/file.json")

    def test_invalid_extension(self):
        
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        tmp.close()
        try:
            loader = FOPFileLoader()
            with pytest.raises(FOPFileLoadError, match="Очікується JSON"):
                loader.load(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_invalid_json(self):
        
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        tmp.write("{invalid json")
        tmp.close()
        try:
            loader = FOPFileLoader()
            with pytest.raises(FOPFileLoadError, match="Невалідний JSON"):
                loader.load(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_load_example_file(self):
        
        example_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "fop_registered.json",
        )
        if os.path.exists(example_path):
            loader = FOPFileLoader()
            result = loader.load(example_path)
            assert len(result) > 0
