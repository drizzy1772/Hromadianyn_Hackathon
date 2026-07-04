from app.services.address_filter import (
    extract_city,
    extract_district,
    extract_region,
    is_target_district,
    parse_address,
)

class TestExtractDistrict:
    def test_shevchenkivskyi_rayon(self):
        address = "м. Київ, Шевченківський район, вул. Хрещатик, 1"
        assert extract_district(address) == "Шевченківський"

    def test_shevchenkivskyi_r_n(self):
        address = "м. Київ, Шевченківський р-н, вул. Хрещатик, 1"
        assert extract_district(address) == "Шевченківський"

    def test_galytskyi(self):
        address = "м. Львів, Галицький район, вул. Свободи, 15"
        assert extract_district(address) == "Галицький"

    def test_no_district(self):
        address = "м. Київ, вул. Хрещатик, 1"
        assert extract_district(address) is None

    def test_empty_address(self):
        assert extract_district("") is None
        assert extract_district(None) is None

class TestExtractRegion:
    def test_kyiv_city(self):
        address = "м. Київ, Шевченківський район, вул. Хрещатик, 1"
        assert extract_region(address) == "м. Київ"

    def test_lvivska_oblast(self):
        address = "Львівська обл., м. Львів, вул. Свободи, 15"
        assert extract_region(address) == "Львівська обл."

    def test_kharkivska_oblast(self):
        address = "Харківська область, м. Харків"
        assert extract_region(address) == "Харківська обл."

    def test_no_region(self):
        assert extract_region("вул. Хрещатик, 1") is None

class TestExtractCity:
    def test_kyiv(self):
        address = "м. Київ, вул. Хрещатик, 1"
        assert extract_city(address) == "Київ"

    def test_lviv(self):
        address = "м. Львів, вул. Свободи, 15"
        assert extract_city(address) == "Львів"

    def test_kyiv_no_space(self):
        address = "м.Київ, вул. Хрещатик"
        assert extract_city(address) == "Київ"

    def test_no_city(self):
        assert extract_city("вул. Хрещатик, 1") is None

class TestIsTargetDistrict:
    def test_match(self):
        address = "м. Київ, Шевченківський район, вул. Хрещатик, 1"
        assert is_target_district(address, "Шевченківський") is True

    def test_no_match(self):
        address = "м. Київ, Подільський район, вул. Щекавицька, 5"
        assert is_target_district(address, "Шевченківський") is False

    def test_no_district(self):
        address = "м. Київ, вул. Хрещатик, 1"
        assert is_target_district(address, "Шевченківський") is False

class TestParseAddress:
    def test_full_address(self):
        address = "м. Київ, Шевченківський район, вул. Хрещатик, 1"
        result = parse_address(address)
        assert result["district"] == "Шевченківський"
        assert result["region"] == "м. Київ"
        assert result["city"] == "Київ"

    def test_lviv_address(self):
        address = "Львівська обл., м. Львів, Галицький район, вул. Свободи, 15"
        result = parse_address(address)
        assert result["district"] == "Галицький"
        assert result["region"] == "Львівська обл."
        assert result["city"] == "Львів"
