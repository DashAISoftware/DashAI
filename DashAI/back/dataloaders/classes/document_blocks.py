"""Group extracted PDF text into blocks and name their element kinds.

A PDF loader can store the text of a page either as one item or as one
item per layout block. Blocks are the finer unit: a paragraph, a heading,
a caption. They keep a converter or an explorer from seeing a whole page
fused into one value, and they let the element kinds of a document mean
something for PDFs.

Blocks never cross a page boundary. The page of an item stays a single
number, and joining blocks that continue across pages belongs to whoever
reads the document, not to the loader.
"""

from collections import Counter
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

PAGE_GRANULARITY = "page"
BLOCK_GRANULARITY = "block"
GRANULARITIES = [PAGE_GRANULARITY, BLOCK_GRANULARITY]

HEADING_RATIO = 1.15
HEADING_MAX_LINES = 3
MAX_HEADING_LEVEL = 6


def split_blank_line_blocks(text: str) -> List[str]:
    """Split page text into blocks separated by blank lines.

    Used by loaders without layout analysis, where the only hint of a block
    boundary is an empty line.

    Parameters
    ----------
    text : str
        Text of one page.

    Returns
    -------
    List[str]
        The stripped non empty blocks, in reading order.
    """
    blocks = []
    current: List[str] = []
    for line in text.splitlines():
        if line.strip():
            current.append(line)
            continue
        if current:
            blocks.append("\n".join(current).strip())
            current = []
    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block]


def representative_size(sizes: Iterable[float]) -> Optional[float]:
    """Return the font size that stands for one block.

    The most common size wins, so a word in a different font does not change
    the size of the block it sits in.

    Parameters
    ----------
    sizes : Iterable[float]
        Size of every character of the block, in points.

    Returns
    -------
    Optional[float]
        The most common size rounded to one decimal, None when the block has
        no sized character.
    """
    return body_size(sizes)


def body_size(sizes: Iterable[float]) -> Optional[float]:
    """Return the font size the document uses for its body text.

    Parameters
    ----------
    sizes : Iterable[float]
        Character size of every line of the document, in points.

    Returns
    -------
    Optional[float]
        The most common size rounded to one decimal, None when no size is
        known.
    """
    counts = Counter(round(size, 1) for size in sizes if size)
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def heading_sizes(
    sizes: Sequence[Optional[float]], body: Optional[float]
) -> List[float]:
    """Return the distinct block sizes that stand out as headings.

    Parameters
    ----------
    sizes : Sequence[Optional[float]]
        Representative size of each block of the document.
    body : Optional[float]
        The body text size, as returned by :func:`body_size`.

    Returns
    -------
    List[float]
        Sizes above the heading threshold, largest first.
    """
    if body is None:
        return []
    standout = {
        round(size, 1)
        for size in sizes
        if size and round(size, 1) >= body * HEADING_RATIO
    }
    return sorted(standout, reverse=True)


def block_element(
    text: str,
    size: Optional[float],
    body: Optional[float],
    ranked: Sequence[float],
) -> Tuple[str, Dict[str, object]]:
    """Name the element kind of one text block.

    A block counts as a heading when it is short and set in a font larger
    than the body text. Its level follows the rank of its size among the
    heading sizes of the document, so the largest heading is level 1.

    Parameters
    ----------
    text : str
        The block text.
    size : Optional[float]
        Representative font size of the block, in points.
    body : Optional[float]
        The body text size of the document.
    ranked : Sequence[float]
        Heading sizes, largest first, as returned by :func:`heading_sizes`.

    Returns
    -------
    Tuple[str, Dict[str, object]]
        The element kind and its attributes.
    """
    if size is None or body is None or not ranked:
        return "paragraph", {}
    if len(text.splitlines()) > HEADING_MAX_LINES:
        return "paragraph", {}
    rounded = round(size, 1)
    if rounded not in ranked:
        return "paragraph", {}
    level = min(list(ranked).index(rounded) + 1, MAX_HEADING_LEVEL)
    return "heading", {"level": level}


def document_body_size(
    blocks: Sequence[Tuple[str, Optional[float]]],
) -> Optional[float]:
    """Return the body text size of a document, weighted by how much text
    each size sets.

    Counting characters rather than blocks keeps a short title set in a large
    font from passing as the body size, however many lines it spans.

    Parameters
    ----------
    blocks : Sequence[Tuple[str, Optional[float]]]
        Each block as its text and its representative font size.

    Returns
    -------
    Optional[float]
        The size that sets the most characters, None when no block has a
        size.
    """
    counts: Counter = Counter()
    for text, size in blocks:
        if size:
            counts[round(size, 1)] += len(text.replace("\n", ""))
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def name_blocks(
    blocks: Sequence[Tuple[str, Optional[float]]],
) -> List[Tuple[str, Dict[str, object]]]:
    """Name the element kind of every block of a document.

    Parameters
    ----------
    blocks : Sequence[Tuple[str, Optional[float]]]
        Each block as its text and its representative font size.

    Returns
    -------
    List[Tuple[str, Dict[str, object]]]
        The kind and attributes of each block, in the same order.
    """
    body = document_body_size(blocks)
    ranked = heading_sizes([size for _, size in blocks], body)
    return [block_element(text, size, body, ranked) for text, size in blocks]
