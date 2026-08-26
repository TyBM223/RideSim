"""Application configuration.

Configuration is read from the process environment exactly once, at first use,
and then treated as immutable for the lifetime of the process. This follows the
12-factor principle of keeping config in the environment rather than in code:
the same built artifact can run in development, staging, and production, and
only the environment differs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version


def _installed_version() -> str:
    """Read the version from installed package metadata.

    The version is declared in exactly one place (pyproject.toml) and read back
    out at runtime, so a released build can never report a version that differs
    from the one it was packaged as. If the package is not installed (someone
    ran the code straight off a checkout), we say so explicitly rather than
    guessing a number that would be wrong.
    """
    try:
        return version("ridesim")
    except PackageNotFoundError:
        return "0.0.0+unknown"


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable application settings.

    `frozen=True` makes the instance hashable and prevents any code path from
    mutating shared config at runtime -- a class of bug that is miserable to
    debug because the symptom appears far from the mutation. `slots=True` drops
    the per-instance __dict__, which is a small memory win and, more usefully,
    turns a typo'd attribute assignment into an AttributeError.
    """

    app_name: str = "RideSim"
    version: str = "0.0.0+unknown"
    environment: str = "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide Settings, building it on first call.

    The cache matters for two reasons. First, os.getenv and importlib.metadata
    lookups are cheap but not free, and this is called on every request that
    depends on it. Second -- and this is the real reason -- FastAPI's dependency
    system compares dependency callables by identity, so returning the *same*
    object every time keeps request handling deterministic and lets tests
    override config by clearing this cache rather than by monkeypatching module
    globals.
    """
    return Settings(
        version=_installed_version(),
        environment=os.getenv("RIDESIM_ENV", "development"),
    )
