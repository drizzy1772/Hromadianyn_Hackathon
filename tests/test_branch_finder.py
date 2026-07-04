from unittest.mock import MagicMock

from app.services.branch_finder import BranchFinder, haversine

class TestHaversine:
    def test_same_point(self):
        
        assert haversine(50.45, 30.52, 50.45, 30.52) == 0.0

    def test_kyiv_to_lviv(self):
        
        distance = haversine(50.4501, 30.5234, 49.8397, 24.0297)
        assert 460 < distance < 480

    def test_kyiv_to_odesa(self):
        
        distance = haversine(50.4501, 30.5234, 46.4825, 30.7233)
        assert 430 < distance < 450

    def test_short_distance(self):
        
        distance = haversine(50.4501, 30.5234, 50.4510, 30.5240)
        assert distance < 1.0

class TestBranchFinder:
    def _make_branch(self, name, lat, lon, city=None, district=None):
        
        branch = MagicMock()
        branch.id = hash(name) % 10000
        branch.name = name
        branch.latitude = lat
        branch.longitude = lon
        branch.city = city
        branch.district = district
        return branch

    def test_find_nearest(self):
        
        branches = [
            self._make_branch("Branch Kyiv", 50.4501, 30.5234, "Київ"),
            self._make_branch("Branch Lviv", 49.8397, 24.0297, "Львів"),
            self._make_branch("Branch Odesa", 46.4825, 30.7233, "Одеса"),
        ]
        finder = BranchFinder(branches)

        branch, distance = finder.find_nearest(50.45, 30.52)
        assert branch.name == "Branch Kyiv"
        assert distance < 5 

    def test_find_nearest_empty(self):
        
        finder = BranchFinder([])
        branch, distance = finder.find_nearest(50.45, 30.52)
        assert branch is None
        assert distance == float("inf")

    def test_find_nearest_n(self):
        
        branches = [
            self._make_branch("A", 50.4501, 30.5234),
            self._make_branch("B", 50.4601, 30.5334),
            self._make_branch("C", 49.8397, 24.0297),
        ]
        finder = BranchFinder(branches)

        result = finder.find_nearest_n(50.45, 30.52, n=2)
        assert len(result) == 2
        assert result[0][1] < result[1][1]

    def test_find_in_city(self):
        
        branches = [
            self._make_branch("A", 50.45, 30.52, city="Київ"),
            self._make_branch("B", 50.46, 30.53, city="Київ"),
            self._make_branch("C", 49.84, 24.03, city="Львів"),
        ]
        finder = BranchFinder(branches)

        result = finder.find_in_city("Київ")
        assert len(result) == 2

    def test_find_in_district(self):
        
        branches = [
            self._make_branch("A", 50.45, 30.52, district="Шевченківський"),
            self._make_branch("B", 50.46, 30.53, district="Подільський"),
        ]
        finder = BranchFinder(branches)

        result = finder.find_in_district("Шевченківський")
        assert len(result) == 1
        assert result[0].name == "A"

    def test_max_distance(self):
        
        branches = [
            self._make_branch("Far Branch", 46.48, 30.72), 
        ]
        finder = BranchFinder(branches)

        branch, distance = finder.find_nearest(50.45, 30.52, max_distance_km=100)
        assert branch is None
