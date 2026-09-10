"""Synchronize credential availability flags on the component registry."""

import logging
from typing import List, Union

from kink import di

logger = logging.getLogger(__name__)


def sync_credentials_status(only: Union[List[str], None] = None) -> None:
    """Refresh ``credentials_satisfied`` flags from stored credential statuses.

    Parameters
    ----------
    only : Union[List[str], None]
        If provided, only these component names are recomputed. If None, all
        components are recomputed.
    """
    store = di["credential_store"]
    registry = di["component_registry"]
    registry.refresh_credentials_status(store.all_statuses(), only=only)
