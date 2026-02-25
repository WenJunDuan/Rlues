"""Gateway layer for HTTP exposure and access control."""

from .http_server import create_app

__all__ = ["create_app"]
