from collections import defaultdict, deque
from functools import wraps
import os
import time
from typing import Optional, Callable, Any, Awaitable, TypeVar, TypedDict, Literal, cast

from typing_extensions import ParamSpec

from fastapi import HTTPException, status, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


P = ParamSpec("P")
R = TypeVar("R")


def _is_testing() -> bool:
    """Return True when running under pytest.

    This helper centralises the detection logic so that rate limiting can
    behave differently in tests (per-test isolation, easier assertions).
    """

    return bool(os.getenv("PYTEST_CURRENT_TEST"))


def rate_limit_key(request: Request) -> str:
    """Return a rate-limit key that isolates pytest runs from each other."""
    if _is_testing():
        current_test = os.getenv("PYTEST_CURRENT_TEST")
        if current_test:
            client_host = request.client.host if request.client else "unknown"
            return f"{current_test}:{client_host}"
    return cast(str, get_remote_address(request))


limiter = Limiter(key_func=rate_limit_key, default_limits=[settings.DEFAULT_RATE_LIMIT])
_test_rate_state: defaultdict[tuple[str, str], deque[float]] = defaultdict(deque)


def _parse_rate_limit(limit: str) -> tuple[int, float]:
    """Parse a SlowAPI-style rate limit string into (count, window_seconds)."""
    try:
        count_str, period = limit.split("/")
        count = int(count_str)
    except ValueError as exc:
        raise ValueError(f"Invalid rate limit format: {limit}") from exc

    period = period.strip().lower()
    if period in {"second", "seconds"}:
        window = 1.0
    elif period in {"minute", "minutes"}:
        window = 60.0
    elif period in {"hour", "hours"}:
        window = 3600.0
    elif period in {"day", "days"}:
        window = 86400.0
    else:
        raise ValueError(f"Unsupported rate limit period: {period}")

    return count, window


def rate_limit(limit: Optional[str]) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator applying per-endpoint rate limiting.

    In tests, a lightweight in-memory implementation is used to avoid relying
    on the global SlowAPI state and to guarantee isolation between tests.
    """

    if limit is None:
        return lambda func: func

    if _is_testing():
        count, window = _parse_rate_limit(limit)

        def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
            @wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | Any:
                request: Optional[Request] = None
                maybe_req: Any = kwargs.get("request")
                if isinstance(maybe_req, Request):
                    request = maybe_req
                else:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break

                if request is None:
                    return await func(*args, **kwargs)

                key = (
                    os.getenv("PYTEST_CURRENT_TEST", "unknown_test"),
                    request.url.path,
                )
                now = time.monotonic()
                bucket = _test_rate_state[key]

                while bucket and now - bucket[0] >= window:
                    bucket.popleft()

                if len(bucket) >= count:
                    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too Many Requests")

                bucket.append(now)
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    return cast(Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]], limiter.limit(limit))


class CookieOptions(TypedDict, total=False):
    httponly: bool
    secure: bool
    samesite: Literal["lax", "strict", "none"]
    domain: str
    max_age: int


def _cookie_options(max_age: int | None = None) -> CookieOptions:
    """Build standard cookie options based on settings."""

    options: CookieOptions = {
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": cast(Literal["lax", "strict", "none"], settings.COOKIE_SAMESITE.lower()),
    }

    if settings.COOKIE_DOMAIN:
        options["domain"] = settings.COOKIE_DOMAIN

    if max_age is not None:
        options["max_age"] = max_age
    elif settings.COOKIE_MAX_AGE is not None:
        options["max_age"] = settings.COOKIE_MAX_AGE

    return options


def _set_auth_cookie(response: Response, value: str, max_age: int | None) -> None:
    """Apply standard auth cookie settings on the response."""

    samesite: Literal["lax", "strict", "none"] = cast(
        Literal["lax", "strict", "none"], settings.COOKIE_SAMESITE.lower()
    )
    domain: Optional[str] = settings.COOKIE_DOMAIN if settings.COOKIE_DOMAIN else None
    effective_max_age: Optional[int] = max_age if max_age is not None else settings.COOKIE_MAX_AGE

    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=value,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=samesite,
        domain=domain,
        max_age=effective_max_age,
    )


def _clear_auth_cookie(response: Response) -> None:
    """Clear the auth cookie using the configured options."""

    options = _cookie_options(max_age=0)
    cookie_parts: list[str] = [
        f"{settings.ACCESS_TOKEN_COOKIE_NAME}=",
        "Path=/",
        'expires="Thu, 01 Jan 1970 00:00:00 GMT"',
        "Max-Age=0",
    ]

    if options.pop("httponly", False):
        cookie_parts.append("HttpOnly")

    samesite = options.pop("samesite", None)
    if isinstance(samesite, str) and samesite:
        cookie_parts.append(f"SameSite={samesite.capitalize()}")

    if options.pop("secure", False):
        cookie_parts.append("Secure")

    domain = options.pop("domain", None)
    if isinstance(domain, str) and domain:
        cookie_parts.append(f"Domain={domain}")

    # max_age already captured above
    options.pop("max_age", None)

    existing_vary = response.headers.get("Vary")
    if existing_vary:
        vary_values = [value.strip() for value in existing_vary.split(",") if value.strip()]
        if not any(value.lower() == "set-cookie" for value in vary_values):
            vary_values.append("set-cookie")
            response.headers["Vary"] = ", ".join(vary_values)
    else:
        response.headers["Vary"] = "set-cookie"
    response.headers.append("set-cookie", "; ".join(cookie_parts))
