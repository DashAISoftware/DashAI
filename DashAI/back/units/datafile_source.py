"""Helpers that find the file to read inside a completed hub download."""

from pathlib import Path
from typing import Optional

from DashAI.back.job.base_job import JobError


def datafile_source_file(datafile_id: int, selected_file: Optional[str]) -> str:
    """Return the path of the file to read from a completed download.

    Re-reads the ``Datafile`` row in a read-only session and never writes to it.

    Parameters
    ----------
    datafile_id : int
        Identifier of the download.
    selected_file : Optional[str]
        File inside the download, relative to its root. None takes the first
        one, ignoring hidden files.

    Returns
    -------
    str
        Absolute path of the chosen file.

    Raises
    ------
    JobError
        If the download does not exist, has not finished, or is empty.
    """
    from kink import di

    from DashAI.back.core.enums.status import DatafileStatus
    from DashAI.back.dependencies.database.models import Datafile

    session_factory = di["session_factory"]

    with session_factory() as db:
        datafile = db.get(Datafile, datafile_id)
        # A missing row and an unfinished download are the same problem from
        # here: there are no files to read either way.
        if datafile is None or datafile.status != DatafileStatus.READY:
            raise JobError(f"Datafile {datafile_id} is not ready.")
        work_dir = datafile.local_path

    return resolve_source_file(work_dir, selected_file)


def resolve_source_file(work_dir: str, selected_file: Optional[str]) -> str:
    """Pick the file to read inside a completed download.

    A plain helper: takes and returns values, never touches the context.

    With no explicit choice it walks the tree and takes the first file in sorted
    order, skipping anything under a dot-prefixed path component — download tools
    leave metadata directories (``.cache``, ``.git``) behind that sort before the
    real data and would otherwise win.

    Parameters
    ----------
    work_dir : str
        Root directory of the download.
    selected_file : Optional[str]
        File inside the download, relative to ``work_dir``.

    Returns
    -------
    str
        Path of the chosen file.

    Raises
    ------
    JobError
        If nothing was selected and the download holds no visible file.
    """
    if selected_file:
        return str(Path(work_dir) / selected_file)

    base = Path(work_dir)
    files = sorted(
        str(path)
        for path in base.rglob("*")
        if path.is_file()
        and not any(part.startswith(".") for part in path.relative_to(base).parts)
    )
    if not files:
        raise JobError("Hub download directory is empty.")
    return files[0]
