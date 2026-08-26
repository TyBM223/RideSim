"""Health endpoint.

Exists so that a process supervisor, container orchestrator, or load balancer
can ask "should I send traffic here?" without exercising real business logic.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ridesim.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response body for GET /health.

    Declared as an explicit model rather than a bare dict so that the response
    shape is (a) validated on the way out, catching a handler that returns the
    wrong thing, and (b) published in the OpenAPI schema, so clients can be
    generated against it.
    """

    status: Literal["ok"] = Field(description="Always 'ok'; a failing process cannot answer.")
    service: str = Field(description="Service name, for when several services share a host.")
    version: str = Field(description="Deployed build version, from package metadata.")
    environment: str = Field(description="Which environment this process believes it is in.")


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    description=(
        "Returns 200 if the process is running and able to serve HTTP. "
        "Does not check downstream dependencies -- there are none yet."
    ),
)
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Report that this process is alive.

    Deliberately does no I/O and touches no shared state, so it stays fast and
    cannot itself become a source of failure. A health check that queries a
    database will report the service as down during a transient database blip,
    causing an orchestrator to kill and restart healthy processes -- which makes
    an outage worse rather than better.
    """
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.version,
        environment=settings.environment,
    )
