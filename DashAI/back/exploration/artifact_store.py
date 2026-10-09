"""Persistence of the render artifacts produced by an exploration.

An explorer builds its renderable output in
:meth:`DashAI.back.exploration.base_explorer.BaseExplorer.get_results`. That
call happens once, when the exploration is created (in the explorer job), and
its result is normalized into artifact wire dicts and written next to the raw
exploration file as ``<explorer_id>_artifacts.json``.

Read requests serve that file directly, so a stored exploration keeps
rendering after its explorer class is removed from the registry (plugin
uninstalled, component dropped from ``config_builder``): only the
:class:`DashAI.back.core.artifacts.Artifact` types, which always exist, are
needed to render it.

Explorations created before the artifacts file existed are upgraded on demand
by :func:`ensure_artifacts` (called from the read endpoints and from the
startup backfill) while their explorer class is still installed.
"""

import json
import logging
import pathlib
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from DashAI.back.dependencies.database.models import Explorer
    from DashAI.back.dependencies.registry import ComponentRegistry
    from DashAI.back.exploration.base_explorer import BaseExplorer

log = logging.getLogger(__name__)

ARTIFACTS_SUFFIX = "_artifacts.json"


def artifacts_path_for(
    exploration_path: Union[str, "pathlib.Path"], explorer_id: Any
) -> pathlib.Path:
    """Build the artifacts file path that belongs to an exploration result.

    Parameters
    ----------
    exploration_path : Union[str, pathlib.Path]
        Path of the raw result file written by ``save_notebook``.
    explorer_id : Any
        Identifier of the explorer record; used as the filename prefix.

    Returns
    -------
    pathlib.Path
        ``<result directory>/<explorer_id>_artifacts.json``.
    """
    path = pathlib.Path(exploration_path)
    directory = path if path.is_dir() else path.parent
    return directory / f"{explorer_id}{ARTIFACTS_SUFFIX}"


def build_artifacts(
    explorer_instance: "BaseExplorer", exploration_path: Union[str, "pathlib.Path"]
) -> List[Dict[str, Any]]:
    """Build the artifact wire dicts of a saved exploration result.

    Parameters
    ----------
    explorer_instance : BaseExplorer
        The instantiated explorer that produced the result.
    exploration_path : Union[str, pathlib.Path]
        Path of the raw result file written by ``save_notebook``.

    Returns
    -------
    List[Dict[str, Any]]
        The normalized artifacts, ready to be serialized as JSON.
    """
    from DashAI.back.core.artifacts import normalize_artifacts

    results = explorer_instance.get_results(
        exploration_path=str(exploration_path), options={}
    )
    return normalize_artifacts(results)


def write_artifacts(
    artifacts_path: Union[str, "pathlib.Path"], artifacts: List[Dict[str, Any]]
) -> str:
    """Write artifact wire dicts to disk as JSON.

    Parameters
    ----------
    artifacts_path : Union[str, pathlib.Path]
        Destination file, usually from :func:`artifacts_path_for`.
    artifacts : List[Dict[str, Any]]
        The artifacts to persist.

    Returns
    -------
    str
        The destination path as a POSIX string.
    """
    path = pathlib.Path(artifacts_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(artifacts, file)
    return path.as_posix()


def read_artifacts(
    artifacts_path: Union[str, "pathlib.Path"],
) -> List[Dict[str, Any]]:
    """Read persisted artifact wire dicts.

    Parameters
    ----------
    artifacts_path : Union[str, pathlib.Path]
        Path of the artifacts file.

    Returns
    -------
    List[Dict[str, Any]]
        The stored artifacts.

    Raises
    ------
    FileNotFoundError
        If the artifacts file does not exist.
    """
    with open(pathlib.Path(artifacts_path), "r", encoding="utf-8") as file:
        return json.load(file)


def store_artifacts(
    explorer_instance: "BaseExplorer",
    exploration_path: Union[str, "pathlib.Path"],
    explorer_id: Any,
) -> str:
    """Build the artifacts of a saved result and persist them next to it.

    Parameters
    ----------
    explorer_instance : BaseExplorer
        The instantiated explorer that produced the result.
    exploration_path : Union[str, pathlib.Path]
        Path of the raw result file written by ``save_notebook``.
    explorer_id : Any
        Identifier of the explorer record; used as the filename prefix.

    Returns
    -------
    str
        Path of the written artifacts file as a POSIX string.
    """
    artifacts = build_artifacts(explorer_instance, exploration_path)
    return write_artifacts(artifacts_path_for(exploration_path, explorer_id), artifacts)


def has_stored_artifacts(explorer: "Explorer") -> bool:
    """Check whether an explorer record has a readable artifacts file.

    Parameters
    ----------
    explorer : Explorer
        The explorer database record.

    Returns
    -------
    bool
        True when ``artifacts_path`` is set and the file exists.
    """
    return (
        bool(explorer.artifacts_path) and pathlib.Path(explorer.artifacts_path).exists()
    )


def ensure_artifacts(
    explorer: "Explorer", explorer_instance: Optional["BaseExplorer"] = None
) -> List[Dict[str, Any]]:
    """Return the stored artifacts of an explorer, generating them if missing.

    Explorations created before artifacts were persisted are upgraded here:
    ``explorer_instance`` is asked for its results once, the artifacts are
    written to disk and ``explorer.artifacts_path`` is set on the record. The
    caller owns the session and must commit.

    Parameters
    ----------
    explorer : Explorer
        The explorer database record, with ``exploration_path`` set.
    explorer_instance : Optional[BaseExplorer]
        Explorer used to build the artifacts. Only needed when the record has
        no stored artifacts yet.

    Returns
    -------
    List[Dict[str, Any]]
        The artifacts of the exploration.

    Raises
    ------
    ValueError
        If the artifacts have to be built and no explorer was given.
    """
    if has_stored_artifacts(explorer):
        return read_artifacts(explorer.artifacts_path)

    if explorer_instance is None:
        raise ValueError(
            f"Explorer {explorer.id} has no stored artifacts and no explorer "
            "instance was given to build them."
        )

    explorer.artifacts_path = store_artifacts(
        explorer_instance, explorer.exploration_path, explorer.id
    )
    log.debug(
        "Backfilled artifacts of explorer %s at %s.",
        explorer.id,
        explorer.artifacts_path,
    )
    return read_artifacts(explorer.artifacts_path)


def ensure_artifacts_from_registry(
    explorer: "Explorer", component_registry: "ComponentRegistry"
) -> List[Dict[str, Any]]:
    """Return the stored artifacts of an explorer, resolving its class if needed.

    The registry is only consulted when the artifacts still have to be built,
    so an exploration with stored artifacts is served even when its explorer
    is no longer registered.

    Parameters
    ----------
    explorer : Explorer
        The explorer database record, with ``exploration_path`` set.
    component_registry : ComponentRegistry
        Registry used to resolve the explorer class for a backfill.

    Returns
    -------
    List[Dict[str, Any]]
        The artifacts of the exploration.

    Raises
    ------
    KeyError
        If a backfill is needed and ``exploration_type`` is not registered,
        i.e. the exploration predates stored artifacts and its explorer is no
        longer installed.
    """
    if has_stored_artifacts(explorer):
        return read_artifacts(explorer.artifacts_path)

    explorer_class = component_registry[explorer.exploration_type]["class"]
    return ensure_artifacts(explorer, explorer_class(**explorer.parameters))


def delete_artifacts(artifacts_path: Union[str, "pathlib.Path", None]) -> None:
    """Delete an artifacts file if it exists.

    Parameters
    ----------
    artifacts_path : Union[str, pathlib.Path, None]
        Path of the artifacts file; ``None`` is a no-op.
    """
    if not artifacts_path:
        return
    path = pathlib.Path(artifacts_path)
    if path.exists() and path.is_file():
        path.unlink()
