"""What loading a package refuses, and what it only warns about."""

import pytest
from sklearn.linear_model import LinearRegression as SklearnLinearRegression

from DashAI.back.model_package.manifest import (
    FORMAT_VERSION,
    MissingPluginError,
    UnsupportedPackageFormatError,
    check_manifest,
    current_versions,
    plugin_distributions,
)
from DashAI.back.models.scikit_learn.linear_regression import LinearRegression


def _manifest(**overrides):
    manifest = {
        "format_version": FORMAT_VERSION,
        "versions": current_versions(),
        "plugins": [],
    }
    manifest.update(overrides)
    return manifest


def test_a_newer_format_is_refused():
    with pytest.raises(UnsupportedPackageFormatError, match="newer"):
        check_manifest(_manifest(format_version=FORMAT_VERSION + 1))


def test_a_missing_plugin_is_named_with_its_install_command():
    plugin = {"name": "dashai-plugin-that-does-not-exist", "version": "1.2.3"}
    with pytest.raises(MissingPluginError) as error:
        check_manifest(_manifest(plugins=[plugin]))
    assert "pip install dashai-plugin-that-does-not-exist==1.2.3" in str(error.value)


def test_a_version_mismatch_only_warns():
    versions = {**current_versions(), "scikit-learn": "0.0.1"}
    with pytest.warns(UserWarning, match="scikit-learn 0.0.1"):
        check_manifest(_manifest(versions=versions))


def test_dashai_classes_are_not_reported_as_plugins():
    assert plugin_distributions([LinearRegression]) == []


def test_a_class_from_another_distribution_is_reported_with_its_version():
    found = plugin_distributions([SklearnLinearRegression])
    assert [p["name"] for p in found] == ["scikit-learn"]
    assert found[0]["version"]
