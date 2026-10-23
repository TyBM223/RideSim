# RideSim

[![ci](https://github.com/TyBM223/RideSim/actions/workflows/ci.yml/badge.svg)](https://github.com/TyBM223/RideSim/actions/workflows/ci.yml)

A real-time driver-to-rider matching and dispatch system, built as a study in
backend, algorithmic, and distributed-systems engineering.

The interesting part of a rideshare backend is not the CRUD. It is: given a ride
request and a fleet of moving drivers, **which driver do you assign, how fast can
you decide, and how do you guarantee you never assign the same driver twice?**
This repository works up to that problem deliberately — measuring before
optimising, and recording why each decision was made.

**Status: Phase 0 — project foundation.** No matching engine yet. See
[Roadmap](#roadmap).

---

## Quick start

Requires Python 3.11+ (developed against 3.14).

```bash
git clone git@github.com:TyBM223/RideSim.git && cd RideSim

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt   # exact locked versions
pip install -e . --no-deps        # the ridesim package itself
```

Run the server:

```bash
uvicorn ridesim.main:app --reload
```

Then visit <http://127.0.0.1:8000/docs> for interactive API documentation, or:

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok","service":"RideSim","version":"0.1.0","environment":"development"}
```

Run the tests and linter:

```bash
pytest
ruff check .
ruff format --check .
```

---

## Architecture

One deployable process — a **modular monolith** — with a strict one-directional
dependency rule. Full reasoning in
[ADR 0002](docs/adr/0002-modular-monolith.md).

```
api  ->  services  ->  domain
              \
               ->  repositories  ->  domain
```

| Layer | Responsibility | May import |
| --- | --- | --- |
| `api/` | HTTP: routing, request/response schemas, status codes | services, domain |
| `services/` | Use cases and orchestration. No HTTP knowledge. | domain, repositories |
| `domain/` | Entities, value objects, algorithms. No framework. | nothing internal |
| `repositories/` | Persistence. Domain-shaped interface. | domain |

Only `api/` exists today. The other directories are created when there is code
that belongs in them — an empty package is a promise the code has not earned.

### Layout

```
src/ridesim/       Application package (src-layout: see note below)
  main.py            Composition root — the only module that wires things together
  config.py          Environment-derived, immutable settings
  api/health.py      Health endpoint
tests/               Test suite
docs/adr/            Architecture Decision Records
pyproject.toml       Abstract deps, package metadata, ruff + pytest config
requirements.txt     Concrete locked deps for reproducible installs
```

**Why `src/`-layout:** the package is not importable from the repository root,
so tests must import the *installed* package. That makes a packaging mistake —
a module missing from the wheel — fail in the test suite rather than in
production. A flat layout hides such mistakes because the working directory is
on `sys.path`.

---

## Design decisions

| ADR | Decision |
| --- | --- |
| [0001](docs/adr/0001-use-fastapi.md) | FastAPI as the HTTP framework |
| [0002](docs/adr/0002-modular-monolith.md) | Modular monolith with an inward dependency rule |
| [0003](docs/adr/0003-synchronous-handlers-first.md) | Synchronous handlers until a measurement justifies async |

---

## Roadmap

Each phase must be justified by a limitation observed in the previous one.

| Phase | Goal | Status |
| --- | --- | --- |
| 0 | Project foundation, health endpoint, test harness | **Done** |
| 1 | Domain model: Driver, Rider, Location, RideRequest, Trip | Next |
| 2 | Core API: registration, location updates, ride requests | |
| 3 | Naive O(n) matching + benchmark | |
| 4 | Ranking and scoring improvements | |
| 5 | PostgreSQL persistence | |
| 6 | Geospatial indexing, measured against the naive baseline | |
| 7 | Concurrency control — no double-assignment under race | |
| 8 | Event-driven behaviour, only if it solves a real problem | |
| 9 | Load testing, profiling, metrics, structured logging | |
| 10 | ML-based ETA prediction | |

---

## Known limitations

Current, deliberate, and tracked:

- **No persistence.** State does not survive a restart. Justified while the
  system has no state worth keeping; revisited in Phase 5.
- **No authentication or authorisation.** Every endpoint is open. Acceptable
  for a health check that reveals nothing sensitive; a blocker before any
  endpoint accepts or returns user data.
- **No rate limiting.** A client can issue unlimited requests.
- **`/health` discloses version and environment.** This is mild information
  disclosure — it helps an attacker fingerprint the build to look up known CVEs.
  It is currently harmless because everything else is open too, but it must be
  restricted at the same time authentication is added.
- **Single process, single machine.** No horizontal scaling story yet.

## License

MIT. See [LICENSE](LICENSE).
