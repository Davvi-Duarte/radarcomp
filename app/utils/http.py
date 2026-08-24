from __future__ import annotations

import logging
import time

import requests

logger = logging.getLogger(__name__)


class HttpClient:
    def __init__(self, timeout: int = 25, retries: int = 2, user_agent: str = "RadarComp/0.1") -> None:
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def get(self, url: str) -> requests.Response:
        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:
                last_exc = exc
                logger.warning("HTTP GET failed (%s/%s) for %s: %s", attempt + 1, self.retries + 1, url, exc)
                if attempt < self.retries:
                    time.sleep(1.5 * (attempt + 1))
        assert last_exc is not None
        raise last_exc
