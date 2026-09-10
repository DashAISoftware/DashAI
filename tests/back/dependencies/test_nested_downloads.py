"""Tests for nested downloadable-component discovery."""

from DashAI.back.dependencies.downloads.nested import (
    iter_config_components,
    missing_downloads,
)


class _Comp:
    """Stand-in component class carrying only download-related attributes."""

    def __init__(self, requires, size=None):
        self.REQUIRES_DOWNLOAD = requires
        self.DOWNLOAD_SIZE_BYTES = size


class _FakeRegistry:
    """Minimal registry: maps names to component classes and download state."""

    def __init__(self, classes, downloaded):
        self._classes = classes
        self._downloaded = downloaded

    def __contains__(self, name):
        return name in self._classes

    def __getitem__(self, name):
        return {"class": self._classes[name]}

    def refresh_download_status(self, name):
        return self._downloaded.get(name, True)


def test_iter_flat_component():
    params = {"tabular_classifier": {"component": "SVC", "params": {}}}
    assert list(iter_config_components(params)) == [("SVC", None)]


def test_iter_unwraps_properties():
    params = {
        "tabular_classifier": {
            "properties": {"component": "SVC", "params": {}},
        }
    }
    assert list(iter_config_components(params)) == [("SVC", None)]


def test_iter_comp_wrapper():
    params = {
        "tabular_classifier": {
            "component": "BagOfWords",
            "params": {"comp": {"component": "SVC", "params": {}}},
        }
    }
    assert list(iter_config_components(params)) == [("SVC", None)]


def test_iter_nested_depth():
    params = {
        "outer": {
            "component": "Wrapper",
            "params": {"inner": {"component": "SVC", "params": {}}},
        }
    }
    names = list(iter_config_components(params))
    assert names == [("Wrapper", None), ("SVC", "Wrapper")]


def test_iter_ignores_primitives_and_fixed_values():
    params = {"n": 5, "alpha": {"fixed_value": 0.1}}
    assert list(iter_config_components(params)) == []


def test_missing_downloads_reports_undownloaded():
    classes = {
        "SVC": _Comp(requires=False),
        "BigNet": _Comp(requires=True, size=42),
    }
    downloaded = {"BigNet": False}
    reg = _FakeRegistry(classes, downloaded)
    params = {
        "a": {"component": "SVC", "params": {}},
        "b": {"component": "BigNet", "params": {}},
    }
    missing = missing_downloads(params, reg)
    assert missing == [{"name": "BigNet", "parent": None, "download_size_bytes": 42}]


def test_missing_downloads_empty_when_all_present():
    classes = {"BigNet": _Comp(requires=True, size=1)}
    reg = _FakeRegistry(classes, {"BigNet": True})
    params = {"b": {"component": "BigNet", "params": {}}}
    assert missing_downloads(params, reg) == []


def test_missing_downloads_dedupes():
    classes = {"BigNet": _Comp(requires=True, size=1)}
    reg = _FakeRegistry(classes, {"BigNet": False})
    params = {
        "a": {"component": "BigNet", "params": {}},
        "b": {"component": "BigNet", "params": {}},
    }
    assert len(missing_downloads(params, reg)) == 1
