# ADR 0003: Write synchronous handlers until a measurement demands otherwise

- **Status:** Accepted
- **Date:** 2026-08-26
- **Phase:** 0

## Context

FastAPI accepts both `def` and `async def` handlers. The common assumption is
that `async def` is the fast one and should always be used.

## Decision

Write handlers as plain `def` until profiling shows a specific I/O-bound
bottleneck that concurrency would relieve.

## Why

The two forms are dispatched differently, and the difference is what matters:

- An `async def` handler runs **directly on the event loop**. It gets true
  concurrency with other requests *only* while it is `await`ing something. Any
  blocking call inside it -- a synchronous DB driver, `time.sleep`, a CPU-heavy
  loop -- blocks the entire event loop, stalling *every* other in-flight request
  in that process. This is the single most common async performance bug.
- A `def` handler is run by Starlette in a **worker thread** from an anyio threadpool.
  It cannot block the event loop, so a blocking call inside it is contained.
  The cost is a thread hop per request and a bounded pool size.

At Phase 0 there is no I/O to overlap: the health handler does arithmetic on
cached config. Async would add an event-loop hop and zero concurrency benefit.
More importantly, `async def` is a *correctness hazard* right up until the
persistence layer is genuinely async — with a synchronous driver like psycopg2,
`async def` is strictly worse than `def`.

Async is also not a fix for CPU-bound work. Ranking a large candidate list is
CPU-bound; running it on the event loop makes latency worse for everyone, and
the CPython GIL means threads will not parallelise it either. That is a
process-level or algorithmic problem, addressed in Phases 6 and 9.

## Alternatives considered

- **`async def` everywhere now.** Rejected: no benefit without `await`, and it
  creates a trap where a later synchronous DB call silently stalls the loop.
- **`async def` with `run_in_threadpool` for blocking parts.** This is what `def`
  already does, written out by hand.

## Revisit when

Phase 5 or 9 shows handler latency dominated by I/O wait, *and* we have an async
driver (e.g. asyncpg). At that point convert the specific hot paths, measure the
change, and record the numbers.
