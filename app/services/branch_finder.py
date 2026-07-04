import logging
import math

from app.db.models import UkrsibBranch

logger = logging.getLogger(__name__)

def haversine(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    
    R = 6371.0 

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

class BranchFinder:

    def __init__(self, branches: list[UkrsibBranch] | None = None):
        
        self.branches = branches or []

    def set_branches(self, branches: list[UkrsibBranch]):
        
        self.branches = branches

    def find_nearest(
        self,
        lat: float,
        lon: float,
        max_distance_km: float | None = None,
    ) -> tuple[UkrsibBranch | None, float]:
        
        if not self.branches:
            logger.warning("Список відділень порожній")
            return None, float("inf")

        nearest_branch = None
        min_distance = float("inf")

        for branch in self.branches:
            if branch.latitude is None or branch.longitude is None:
                continue

            distance = haversine(lat, lon, branch.latitude, branch.longitude)

            if distance < min_distance:
                min_distance = distance
                nearest_branch = branch

        if max_distance_km and min_distance > max_distance_km:
            logger.info(
                f"Найближче відділення на відстані {min_distance:.1f} км "
                f"(перевищує ліміт {max_distance_km} км)"
            )
            return None, min_distance

        if nearest_branch:
            logger.debug(
                f"Найближче відділення: '{nearest_branch.name}' "
                f"({min_distance:.1f} км)"
            )

        return nearest_branch, min_distance

    def find_nearest_n(
        self,
        lat: float,
        lon: float,
        n: int = 3,
    ) -> list[tuple[UkrsibBranch, float]]:
        
        if not self.branches:
            return []

        distances: list[tuple[UkrsibBranch, float]] = []

        for branch in self.branches:
            if branch.latitude is None or branch.longitude is None:
                continue
            distance = haversine(lat, lon, branch.latitude, branch.longitude)
            distances.append((branch, distance))

        distances.sort(key=lambda x: x[1])
        return distances[:n]

    def find_in_city(
        self,
        city: str,
    ) -> list[UkrsibBranch]:
        
        city_lower = city.lower().strip()
        return [
            branch
            for branch in self.branches
            if branch.city and branch.city.lower().strip() == city_lower
        ]

    def find_in_district(
        self,
        district: str,
    ) -> list[UkrsibBranch]:
        
        district_lower = district.lower().strip()
        return [
            branch
            for branch in self.branches
            if branch.district
            and branch.district.lower().strip() == district_lower
        ]
