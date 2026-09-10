"""Atomic file and directory write helpers.

Use these when writing outputs that must not be left in a corrupt state if the
process is killed mid-write (e.g. during job cancellation).
"""

import os
import secrets
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Union


@contextmanager
def atomic_open(path: Union[str, Path], mode: str = "wb"):
    """Context manager for atomically writing a single file.

    Writes to a sibling temp file and renames it to *path* on clean close.
    If the context body raises, the temp file is deleted and *path* is untouched.

    Usage::

        with atomic_open(output_path, "wb") as f:
            pickle.dump(data, f)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_")
    try:
        with os.fdopen(tmp_fd, mode) as f:
            yield f
        os.replace(tmp_path, path)
    except BaseException:
        with SuppressErrors():
            os.unlink(tmp_path)
        raise


@contextmanager
def atomic_directory(final_path: Union[str, Path]):
    """Context manager for atomically writing a directory tree.

    Yields an *existing* temporary directory path.  The caller writes files
    into it.  On clean exit, *final_path* is replaced safely:

    1. The existing *final_path* (if any) is renamed to a sibling temp name —
       so the old data is never destroyed before the new data is in place.
    2. *tmp_dir* is renamed to *final_path*.
    3. The old sibling is deleted (new data is already live at *final_path*).

    On error the temp dir is removed and *final_path* is untouched (or still
    holds whichever copy was live at the time of the kill).

    Usage::

        with atomic_directory(dataset_dir) as tmp_dir:
            # tmp_dir already exists; write files into it
            (tmp_dir / "data.arrow").write_bytes(...)
    """
    final_path = Path(final_path)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(dir=final_path.parent, prefix=".tmp_"))
    try:
        yield tmp_dir
        # Step 1: move the existing target out of the way (never destroy first)
        old_path = None
        if final_path.exists():
            old_path = final_path.parent / f".old_{secrets.token_hex(6)}"
            final_path.rename(old_path)
        # Step 2: install new data (old data is safe at old_path if step 1 ran)
        tmp_dir.rename(final_path)
        # Step 3: delete old data now that new data is live
        if old_path is not None:
            with SuppressErrors():
                shutil.rmtree(old_path, ignore_errors=True)
    except BaseException:
        with SuppressErrors():
            shutil.rmtree(tmp_dir, ignore_errors=True)
        raise


@contextmanager
def atomic_save_path(final_path: Union[str, Path]):
    """Context manager for atomically replacing a file OR directory.

    Yields a *non-existent* sibling temp path.  The caller creates whatever it
    needs there (a file, a directory tree, etc.).  On clean exit, *final_path*
    is replaced atomically.  On error, the temp artifact is removed.

    Use this when the callee controls path creation (e.g. model.save(path) may
    write a joblib file or a directory of weights depending on model type).

    Usage::

        with atomic_save_path(run_path) as tmp:
            model.save(str(tmp))  # model decides whether tmp is a file or dir
    """
    final_path = Path(final_path)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    # No leading dot: torch.save() derives the zip's internal archive name by
    # stripping everything from the last dot, so a name like '.tmp_ab12cd' ends
    # up empty and PyTorchFileWriter rejects it with 'invalid file name'.
    tmp_path = final_path.parent / f"tmp_{secrets.token_hex(6)}.partial"
    try:
        yield tmp_path
        # Rename-before-delete: move the existing artifact aside first so it is
        # never destroyed before the new one is in place (same as atomic_directory).
        old_path = None
        if final_path.exists() or final_path.is_symlink():
            old_path = final_path.parent / f".old_{secrets.token_hex(6)}"
            final_path.rename(old_path)
        tmp_path.rename(final_path)
        if old_path is not None:
            with SuppressErrors():
                if old_path.is_dir():
                    shutil.rmtree(old_path, ignore_errors=True)
                else:
                    old_path.unlink()
    except BaseException:
        with SuppressErrors():
            if tmp_path.is_dir():
                shutil.rmtree(tmp_path, ignore_errors=True)
            elif tmp_path.exists():
                tmp_path.unlink()
        raise


class SuppressErrors:
    """Silently swallows all exceptions (like contextlib.suppress(Exception))."""

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return True
