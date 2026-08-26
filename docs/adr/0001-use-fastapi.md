# ADR 0001: Use FastAPI as the HTTP framework

- **Status:** Accepted
- **Date:** 2026-08-26
- **Phase:** 0

## Context

RideSim is an HTTP service. It needs to parse and validate untrusted request
bodies (coordinates, IDs, state transitions), serialise responses, and publish a
machine-readable API contract. Later phases add I/O-bound concurrency: many
simultaneous driver location updates, each mostly waiting on a database.

## Decision

Use FastAPI (on Starlette/ASGI), served by uvicorn.

## Why

1. **Validation is not optional and should not be hand-written.** Every field
   arriving from a client is untrusted. FastAPI derives validation from the same
   Pydantic type annotations used for documentation, so the validator and the
   documented contract cannot drift apart. Hand-rolled `if "lat" not in body`
   checks drift the moment someone forgets one, and a missing check on a
   latitude field is a real bug: it propagates a `None` into distance maths.
2. **ASGI gives us an async path when we need it.** Matching is I/O-bound
   (database round-trips, later a cache). ASGI lets one process interleave
   thousands of in-flight requests that are blocked on I/O. We are *not* using
   async yet -- see ADR 0003 -- but choosing a WSGI framework now would mean
   changing frameworks later to get it.
3. **OpenAPI generation is free.** The schema is a genuine artifact: it drives
   `/docs`, client generation, and contract tests.

## Alternatives considered

- **Flask.** Mature and simple, but WSGI (one request per worker thread while
  blocked on I/O) and validation/serialisation are bolt-ons (marshmallow,
  flask-smorest) that must be kept in sync by hand.
- **Django + DRF.** Brings an ORM, admin, auth, and migrations. That is a lot of
  value, but RideSim's hard problems are algorithmic and geospatial, not CRUD
  scaffolding. The ORM in particular would get in the way of the hand-written
  spatial queries planned for Phase 6.
- **Bare Starlette.** FastAPI *is* Starlette plus validation and OpenAPI. Using
  Starlette directly means re-implementing exactly the parts we want.

## Consequences

- We inherit Pydantic v2 as a hard dependency; its validation cost sits on every
  request and will show up in Phase 9 latency profiling. `pydantic-core` is
  compiled Rust, so this cost is small, but it is not zero and we should measure
  it rather than assume.
- FastAPI's `Depends` becomes the injection mechanism for config and, later,
  repositories. That is a framework-specific idiom leaking into handler
  signatures -- acceptable in the API layer, which is allowed to know about the
  framework, and forbidden below it.
