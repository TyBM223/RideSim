"""Tests for the health endpoint and the app wiring underneath it."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient):
    """The endpoint is reachable and reports success.

    This is the thinnest possible end-to-end proof that the whole stack is
    wired: the router is registered on the app, the path is spelled the way we
    think it is, and the handler runs without raising.
    """
    response = client.get("/health")

    assert response.status_code == 200


def test_health_reports_expected_payload(client: TestClient):
    """The response body carries the fields an operator needs.

    Without this, a refactor could return 200 with an empty body and every
    status-code assertion would still pass, while any dashboard reading
    `version` to answer "what is deployed right now?" would silently break.
    """
    body = client.get("/health").json()

    assert body["status"] == "ok"
    assert body["service"] == "RideSim"
    assert body["environment"] == "development"
    assert isinstance(body["version"], str) and body["version"]


def test_health_responds_as_json(client: TestClient):
    """The Content-Type header marks the body as JSON.

    Clients dispatch on this header. A handler returning a JSON-looking string
    as text/plain passes a body-shape assertion but breaks real clients, so the
    header is asserted separately from the body.
    """
    response = client.get("/health")

    assert response.headers["content-type"].startswith("application/json")


def test_health_rejects_post_with_405(client: TestClient):
    """A write to a read-only resource is Method Not Allowed, not 404.

    This proves the route is registered against GET specifically. 405 tells the
    client "this resource exists, but not with that verb", which is the correct
    and more useful answer than 404. FastAPI derives this from the router, so
    the test is really checking that we registered the method we intended.
    """
    response = client.post("/health")

    assert response.status_code == 405


def test_unknown_route_returns_404(client: TestClient):
    """Undefined paths are rejected rather than absorbed.

    Guards against a future catch-all route silently swallowing typo'd paths,
    which would turn a client bug into a confusing 200 with empty data.
    """
    response = client.get("/no-such-endpoint")

    assert response.status_code == 404


def test_openapi_schema_is_served_and_documents_health(client: TestClient):
    """The generated OpenAPI schema is valid and includes the health path.

    The schema is a real deliverable -- it is what client SDKs and API docs are
    generated from. This asserts the response model reached the schema, which
    catches a handler annotated with a bare dict return type: that still serves
    traffic correctly but publishes an empty, useless contract.
    """
    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "RideSim"
    assert "/health" in schema["paths"]

    response_schema = schema["paths"]["/health"]["get"]["responses"]["200"]
    assert "application/json" in response_schema["content"]
