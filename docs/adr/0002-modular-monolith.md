# ADR 0002: Build a modular monolith with an inward dependency rule

- **Status:** Accepted
- **Date:** 2026-08-26
- **Phase:** 0

## Context

RideSim will eventually have several distinguishable concerns: driver
registry, rider registry, geospatial search, matching/ranking, trip lifecycle,
and metrics. A common instinct is to make each a service. Another is to put
everything in one file until it hurts.

## Decision

One deployable process, internally divided into layers with a one-directional
dependency rule:

```
api  ->  services  ->  domain
              \\
               ->  repositories  ->  domain
```

- **`api/`** -- HTTP concerns only: routing, request/response schemas, status
  codes. May import from `services` and `domain`. Nothing imports *from* `api`.
- **`services/`** -- use cases and orchestration (e.g. "match this request to a
  driver"). Knows nothing about HTTP; must be callable from a test, a CLI, or a
  background worker.
- **`domain/`** -- entities, value objects, and pure business rules. Imports
  nothing from the layers above and no framework. This is where the algorithms
  live.
- **`repositories/`** -- persistence. Interface expressed in domain terms;
  implementation may be a dict now and Postgres later.

Only `api/` and `config` exist at Phase 0. The remaining directories are
**deliberately not created yet** -- empty packages are a promise the code has
not earned.

## Why

The dependency rule is the whole point, and it is cheap to enforce now and
expensive to retrofit. Its practical payoffs:

- **Testability.** Matching logic that does not import FastAPI can be tested
  without an HTTP client, which means microsecond unit tests and benchmarks that
  measure the algorithm rather than the framework. This matters directly for
  Phases 3, 4, and 6, where we benchmark matching.
- **Swappability.** Phase 5 replaces an in-memory store with Postgres. If the
  service layer depends on a repository *interface* stated in domain terms, that
  swap touches one implementation. If handlers reach into a global dict, it
  touches everything.
- **It is the honest precursor to services.** Clean module seams are what make a
  later extraction mechanical. Seams first, network later -- if ever.

## Alternatives considered

- **Microservices now.** Rejected. Splitting introduces network latency, partial
  failure, retries, duplicate delivery, distributed tracing, and deployment
  orchestration *before* there is any load, team-size, or scaling pressure to
  justify them. A "driver service" and "matching service" that only ever talk to
  each other are a single service with extra serialisation and new failure
  modes. We will revisit only when a concrete pressure appears -- e.g. matching
  needs different hardware or a different scaling curve than the CRUD endpoints.
- **Single `main.py`.** Fine for a week. The cost lands when matching needs a
  benchmark and the only way to call it is through an HTTP request, which mixes
  framework overhead into every measurement.
- **Full hexagonal/ports-and-adapters with protocols everywhere.** Rejected as
  premature. There is exactly one implementation of everything today; an
  interface with one implementer is indirection without benefit. We will
  introduce the interface at the moment the second implementation appears.

## Consequences

- Some code will feel indirect at small scale (a service method that only calls
  a repository method). Accepted deliberately.
- The rule needs enforcement to stay true. For now it is convention plus review;
  if it starts drifting, an import-linter rule in CI is the cheap fix.
