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


def check_manifest(manifest: Dict[str, Any]) -> None:
    """Refuse a package this installation cannot load; warn on version drift.

    Raises
    ------
    UnsupportedPackageFormatError
        If the package format is newer than this DashAI understands.
    MissingPluginError
        If a plugin the package was built from is not installed.
    """
    format_version = manifest.get("format_version")
    if not isinstance(format_version, int) or format_version > FORMAT_VERSION:
        raise UnsupportedPackageFormatError(
            f"This model package uses format {format_version!r}, which is newer "
            f"than the one this DashAI reads ({FORMAT_VERSION}). Update DashAI "
            "to load it."
        )

    for plugin in manifest.get("plugins", []):
        if installed_version(plugin["name"]) is None:
            requirement = plugin["name"]
            if plugin.get("version"):
                requirement += f"=={plugin['version']}"
            raise MissingPluginError(
                f"This model needs the plugin '{plugin['name']}'. "
                f"Install it with: pip install {requirement}"
            )

    for name, expected in manifest.get("versions", {}).items():
        actual = _python_version() if name == "python" else installed_version(name)
        if actual != expected:
            warnings.warn(
                f"The model was exported with {name} {expected}, but "
                f"{actual or 'no version'} is installed. Loading or predicting "
                "may fail or give different results.",
                UserWarning,
                stacklevel=3,
            )
