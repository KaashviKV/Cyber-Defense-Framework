"""
HTTP helper with retry support for external CTI APIs.
"""

import time
from typing import Any, Optional

import requests

from backend.config.config import CTI_REQUEST_TIMEOUT, CTI_RETRY_ATTEMPTS


def request_with_retry(
    method: str,
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    params: Optional[dict[str, Any]] = None,
    timeout: int = CTI_REQUEST_TIMEOUT,
    attempts: int = CTI_RETRY_ATTEMPTS,
) -> requests.Response:
    """
    Perform an HTTP request with simple retry on transient failures.
    Raises requests.RequestException on final failure.
    """
    last_exc: Optional[Exception] = None
    max_attempts = max(1, attempts)

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=timeout,
            )

            if response.status_code in {429, 500, 502, 503, 504} and attempt < max_attempts:
                time.sleep(0.5 * attempt)
                continue

            return response

        except requests.RequestException as exc:
            last_exc = exc
            if attempt >= max_attempts:
                raise
            time.sleep(0.5 * attempt)

    if last_exc:
        raise last_exc

    raise requests.RequestException("Request failed after retries.")
