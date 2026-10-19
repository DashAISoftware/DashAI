"""Scratch directories for tests that load datasets.

Dataloaders take a ``temp_path`` and hand it straight to HuggingFace as
``cache_dir`` (see ``CSVDataLoader.load_data``), so every test that loads a
dataset leaves an arrow cache and a ``dataset_info.json`` behind. Pointing that
path at the system temp directory keeps those artifacts out of the repository
tree instead of scattering them across ``tests/back/``.
"""

import os
import pathlib
import shutil
import tempfile

# Scoped by pid so two pytest processes running at once (two terminals, a CI
# matrix on one machine) never share a root: without this, one session's
# start-of-run ``clear_scratch()`` would rmtree the arrow cache another,
# still-running session has memory mapped.
SCRATCH_ROOT = (
    pathlib.Path(tempfile.gettempdir()) / f"dashai-test-scratch-{os.getpid()}"
)


def scratch_dir(*parts: str) -> str:
    """Return a scratch directory, creating it if it does not exist.

    Parameters
    ----------
    *parts : str
        Path segments below the scratch root. Use them to keep unrelated test
        modules from sharing a cache, the way the old in-repo paths did.

    Returns
    -------
    str
        Absolute path to the directory.
    """
    path = SCRATCH_ROOT.joinpath(*parts)
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def clear_scratch() -> None:
    """Remove the scratch root, ignoring files still held open.

    Arrow caches stay memory mapped on Windows, so a best effort delete is the
    most that can be promised here; the point is that whatever survives lives
    outside the repository.
    """
    shutil.rmtree(SCRATCH_ROOT, ignore_errors=True)
