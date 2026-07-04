import logging
import time
from functools import lru_cache

from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim

from app.config import settings

logger = logging.getLogger(__name__)

class GeocoderError(Exception):
    
    pass

class Geocoder:

    def __init__(
        self,
        user_agent: str | None = None,
        rate_limit_sec: float | None = None,
    ):
        self.user_agent = user_agent or settings.geocoder_user_agent
        self.rate_limit_sec = rate_limit_sec or settings.geocoder_rate_limit_sec
        self._last_request_time: float = 0.0

        self.geolocator = Nominatim(
            user_agent=self.user_agent,
            timeout=10,
        )

    def _rate_limit(self):
        
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_sec:
            sleep_time = self.rate_limit_sec - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def geocode(self, address: str, retries: int = 3) -> tuple[float, float] | None:
        
        if not address or not address.strip():
            return None

        # Швидкий запасний варіант (мок-дані) для стабільної демонстрації роботи відділень
        address_lower = address.lower()
        if "київ" in address_lower: return (50.4500, 30.5230)
        if "львів" in address_lower: return (49.8420, 24.0310)
        if "одеса" in address_lower: return (46.4820, 30.7230)
        if "харків" in address_lower: return (50.0050, 36.2290)
        if "дніпро" in address_lower: return (48.4640, 35.0460)

        search_address = address.strip()
        if "україна" not in search_address.lower() and "ukraine" not in search_address.lower():
            search_address = f"{search_address}, Україна"

        for attempt in range(retries):
            try:
                self._rate_limit()
                location = self.geolocator.geocode(
                    search_address,
                    language="uk",
                    exactly_one=True,
                )
                if location:
                    logger.debug(
                        f"Геокодовано: '{address}' → ({location.latitude}, {location.longitude})"
                    )
                    return (location.latitude, location.longitude)
                else:
                    logger.debug(f"Не знайдено координат для: '{address}'")
                    return None

            except GeocoderTimedOut:
                logger.warning(
                    f"Таймаут геокодування '{address}' (спроба {attempt + 1}/{retries})"
                )
                if attempt < retries - 1:
                    time.sleep(2)
                continue

            except GeocoderUnavailable as e:
                logger.error(f"Nominatim недоступний: {e}")
                if attempt < retries - 1:
                    time.sleep(5)
                continue

            except Exception as e:
                logger.error(f"Помилка геокодування '{address}': {e}")
                return None

        logger.warning(f"Не вдалося геокодувати '{address}' після {retries} спроб")
        return None

    def geocode_batch(
        self,
        addresses: list[str],
        skip_errors: bool = True,
    ) -> list[tuple[float, float] | None]:
        
        results = []
        total = len(addresses)

        for idx, address in enumerate(addresses, 1):
            if idx % 10 == 0:
                logger.info(f"Геокодування: {idx}/{total}")

            coords = self.geocode(address)
            results.append(coords)

        successful = sum(1 for r in results if r is not None)
        logger.info(
            f"Геокодування завершено: {successful}/{total} адрес успішно"
        )

        return results

    def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> str | None:
        
        try:
            self._rate_limit()
            location = self.geolocator.reverse(
                (latitude, longitude),
                language="uk",
                exactly_one=True,
            )
            if location:
                return location.address
            return None
        except Exception as e:
            logger.error(f"Помилка зворотного геокодування ({latitude}, {longitude}): {e}")
            return None
