"""Layout of an exported model package and the checks run before loading one.

A package is a zip holding a trained model, the session preprocessor it was
trained behind, the training column types and this manifest. The manifest is
what lets a package be judged before anything in it is unpickled: whether this
DashAI can read its format, whether the plugins it was built from are
installed, and which library versions it was trained with.
"""

import importlib.metadata
import sys
import warnings
from typing import Any, Dict, Iterable, List, Optional

FORMAT_VERSION = 1
# What a DashAI file holds. Files written before kinds existed are models.
KIND_MODEL = "model"
PACKAGE_EXTENSION = ".dashai-model"

MANIFEST_ENTRY = "manifest.json"
MODEL_ENTRY = "model"
PREPROCESSOR_ENTRY = "preprocessing/final.pkl"
# Mirrors a DashAI dataset folder ("<dataset>/dataset/data.arrow") so the
# existing readers (load_dataset, get_columns_spec) open it unchanged.
SCHEMA_ENTRY = "schema/dataset"

DASHAI_DISTRIBUTION = "dashAI"
TRACKED_LIBRARIES = ("scikit-learn", "torch", "transformers")


class ModelPackageError(Exception):
    """A file cannot be used as a DashAI model package."""


class WrongPackageKindError(ModelPackageError):
    """The file is a DashAI file of another kind (a session, not a model)."""


class UnsupportedPackageFormatError(ModelPackageError):
    """The package was written by a newer DashAI than the installed one."""


class MissingPluginError(ModelPackageError):
    """The package needs a plugin distribution that is not installed."""


def installed_version(distribution: str) -> Optional[str]:
    """Return the installed version of a distribution, or None if absent."""
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _python_version() -> str:
    # Major.minor only: a patch release never changes what unpickles.
    return f"{sys.version_info.major}.{sys.version_info.minor}"


def current_versions() -> Dict[str, str]:
    """Versions of Python, DashAI and the tracked ML libraries installed now."""
    versions = {"python": _python_version()}
    for distribution in (DASHAI_DISTRIBUTION, *TRACKED_LIBRARIES):
        version = installed_version(distribution)
        if version is not None:
            versions[distribution] = version
    return versions


def plugin_distributions(classes: Iterable[type]) -> List[Dict[str, Optional[str]]]:
    """Distributions outside DashAI that provide the given classes.

    A class defined in DashAI itself needs nothing extra; any other one comes
    from an installed distribution (a plugin) that whoever loads the package
    must also have.
    """
    providers = importlib.metadata.packages_distributions()
    found: Dict[str, Optional[str]] = {}
    for cls in classes:
        top_level = cls.__module__.split(".")[0]
        if top_level == "DashAI":
            continue
        for distribution in providers.get(top_level, []):
            found[distribution] = installed_version(distribution)
    return [{"name": name, "version": found[name]} for name in sorted(found)]


def check_manifest(
    manifest: Dict[str, Any],
    kind: str = KIND_MODEL,
    format_version: int = FORMAT_VERSION,
) -> None:
    """Refuse a file this installation cannot load; warn on version drift.

    Parameters
    ----------
    manifest : dict
        The file's parsed ``manifest.json``.
    kind : str
        The kind of file the caller expects.
    format_version : int
        The newest format of that kind this DashAI reads.

    Raises
    ------
    WrongPackageKindError
        If the file is a DashAI file of another kind.
    UnsupportedPackageFormatError
        If the file format is newer than this DashAI understands.
    MissingPluginError
        If a plugin the file was built from is not installed.
    """
    found = manifest.get("kind", KIND_MODEL)
    if found != kind:
        raise WrongPackageKindError(
            f"This file is a DashAI {found} file, not a {kind} file."
        )

    version = manifest.get("format_version")
    if not isinstance(version, int) or version > format_version:
        raise UnsupportedPackageFormatError(
            f"This file uses format {version!r}, which is newer than the one "
            f"this DashAI reads ({format_version}). Update DashAI to load it."
        )

    for plugin in manifest.get("plugins", []):
        if installed_version(plugin["name"]) is None:
            requirement = plugin["name"]
            if plugin.get("version"):
                requirement += f"=={plugin['version']}"
            raise MissingPluginError(
                f"This file needs the plugin '{plugin['name']}'. "
                f"Install it with: pip install {requirement}"
            )

    for name, expected in manifest.get("versions", {}).items():
        actual = _python_version() if name == "python" else installed_version(name)
        if actual != expected:
            warnings.warn(
                f"The file was exported with {name} {expected}, but "
                f"{actual or 'no version'} is installed. Loading or predicting "
                "may fail or give different results.",
                UserWarning,
                stacklevel=3,
            )
