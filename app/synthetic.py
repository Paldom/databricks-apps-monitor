"""Request metadata and app-route selection for monitor-generated traffic."""

from urllib.parse import unquote, urlsplit


def synthetic_headers(headers: dict, kind: str) -> dict:
    return {**headers, "x-monitor-synthetic": kind}


def capacity_path(value: str | None) -> str:
    if value is not None and not isinstance(value, str):
        raise ValueError("capacity_path must be a string")
    path = value or "/"
    parsed = urlsplit(path)
    if (
        not path.startswith("/")
        or path.startswith("//")
        or parsed.scheme
        or parsed.netloc
        or "\\" in path
        or any(ord(c) < 32 for c in path)
        or unquote(parsed.path).rstrip("/").lower() == "/healthz"
    ):
        raise ValueError("capacity_path must be an app-relative path other than /healthz")
    return path


async def capacity_url(client, base: str, fallback: str | None, headers: dict) -> str:
    """Only missing routes fall back; unhealthy app responses must remain visible."""
    fallback = capacity_path(fallback)
    url = base.rstrip("/") + "/monitor/health"
    response = await client.get(url, headers=synthetic_headers(headers, "capacity"))
    if response.status_code in (404, 405) or (
        response.status_code == 200 and "text/html" in response.headers.get("content-type", "")
    ):
        return base.rstrip("/") + fallback
    return url
