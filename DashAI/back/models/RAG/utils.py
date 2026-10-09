import hashlib


def hash_function(content: str | bytes) -> str:
    """Generate a SHA-256 hash for the given content.

    Args:
        content: The content to hash (str or bytes).

    Returns:
        A hex-encoded SHA-256 hash string.

    Raises:
        UnicodeEncodeError: If a str content cannot be encoded as UTF-8.
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()
