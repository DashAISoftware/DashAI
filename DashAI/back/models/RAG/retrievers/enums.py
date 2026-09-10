"""Enum definitions for retriever configuration."""

from enum import Enum


class MergeStrategy(str, Enum):
    """Strategies for merging results from parallel retrievers.

    Attributes:
        ROUND_ROBIN: Alternates results from each child retriever.
        INTERLEAVE: Concatenates child results preserving internal order.
    """

    ROUND_ROBIN = "round_robin"
    INTERLEAVE = "interleave"
