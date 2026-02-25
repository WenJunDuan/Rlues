"""HTTP utility skeleton with unified response envelope."""


def request(method: str, url: str, **kwargs) -> dict:
    return {
        "ok": False,
        "code": "NOT_IMPLEMENTED",
        "message": "http_client.request not implemented",
        "data": {"method": method, "url": url, "kwargs": kwargs},
        "meta": {"plugin": "http_client"},
    }
