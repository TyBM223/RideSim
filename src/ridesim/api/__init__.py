"""HTTP layer: routers, request/response schemas, and status-code mapping.

Nothing in this package may be imported by the domain or service layers. The
dependency arrow points inward only: api -> services -> domain.
"""
