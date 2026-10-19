"""App-wide runtime options the frontend reads on load."""

import os

from fastapi import APIRouter

router = APIRouter()

_TRUTHY = {"1", "true", "yes", "on"}


def tours_autostart_enabled() -> bool:
    """Whether guided tours may open by themselves on a first visit.

    Disabled by ``--no-tours`` / ``-nt`` on the CLI, which sets
    ``DASHAI_NO_TOURS`` (the variable can also be set directly). Tours stay
    available from the navbar help button either way.
    """
    return os.environ.get("DASHAI_NO_TOURS", "").strip().lower() not in _TRUTHY


@router.get("/")
async def get_app_config() -> dict:
    """Return the runtime options that change frontend behaviour.

    Returns
    -------
    dict
        ``tours_autostart``: whether tours open automatically on first visit.
    """
    return {"tours_autostart": tours_autostart_enabled()}
