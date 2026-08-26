"""Composition root.

This is the only module that knows how the pieces fit together. Routers,
config, and (later) services and repositories are wired here and nowhere else,
so that every other module can be imported and tested without dragging in the
whole application.
"""

from __future__ import annotations

from fastapi import FastAPI

from ridesim.api import health
from ridesim.config import get_settings


def create_app() -> FastAPI:
    """Build a fully wired FastAPI application.

    This is the application-factory pattern. The alternative -- constructing a
    module-level `app` directly and mutating it with decorators at import time
    -- works, but it makes the application a process-wide singleton that is
    created as a side effect of importing. That is fine until a test needs an
    instance with different config or a clean in-memory store, at which point
    the only escape is monkeypatching. A factory costs one function and removes
    that problem before it appears.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Real-time driver-to-rider matching and dispatch.",
    )

    app.include_router(health.router)

    return app


# Module-level instance for ASGI servers, which need an import path to an
# application object: `uvicorn ridesim.main:app`.
app = create_app()
