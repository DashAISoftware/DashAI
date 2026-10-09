import os
import pathlib
import sys

import pytest

from DashAI.back.plugins.environment import (
    activate_plugins_directory,
    get_plugins_directory,
)

INTERPRETER_DIR = f"py{sys.version_info.major}.{sys.version_info.minor}"


@pytest.fixture(autouse=True)
def _restore_import_state():
    original_path = list(sys.path)
    original_pythonpath = os.environ.get("PYTHONPATH")
    yield
    sys.path[:] = original_path
    if original_pythonpath is None:
        os.environ.pop("PYTHONPATH", None)
    else:
        os.environ["PYTHONPATH"] = original_pythonpath


def test_get_plugins_directory_uses_the_local_path_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHAI_LOCAL_PATH", str(tmp_path))

    assert get_plugins_directory() == tmp_path / "plugins" / INTERPRETER_DIR


def test_get_plugins_directory_prefers_the_explicit_local_path(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHAI_LOCAL_PATH", str(tmp_path / "ignored"))

    directory = get_plugins_directory(tmp_path / "explicit")

    assert directory == tmp_path / "explicit" / "plugins" / INTERPRETER_DIR


def test_get_plugins_directory_falls_back_to_the_home_directory(monkeypatch):
    monkeypatch.delenv("DASHAI_LOCAL_PATH", raising=False)

    directory = get_plugins_directory()

    expected = pathlib.Path("~/.DashAI").expanduser().absolute()
    assert directory == expected / "plugins" / INTERPRETER_DIR


def test_activate_plugins_directory_makes_the_directory_importable(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DASHAI_LOCAL_PATH", str(tmp_path))
    monkeypatch.delenv("PYTHONPATH", raising=False)

    directory = activate_plugins_directory()

    assert directory.is_dir()
    assert str(directory) in sys.path
    assert os.environ["PYTHONPATH"].split(os.pathsep)[0] == str(directory)


def test_activate_plugins_directory_keeps_existing_pythonpath_entries(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("DASHAI_LOCAL_PATH", str(tmp_path))
    monkeypatch.setenv("PYTHONPATH", "/somewhere/else")

    directory = activate_plugins_directory()

    assert os.environ["PYTHONPATH"] == os.pathsep.join(
        [str(directory), "/somewhere/else"]
    )


def test_activate_plugins_directory_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHAI_LOCAL_PATH", str(tmp_path))
    monkeypatch.delenv("PYTHONPATH", raising=False)

    directory = activate_plugins_directory()
    activate_plugins_directory()

    assert sys.path.count(str(directory)) == 1
    assert os.environ["PYTHONPATH"].count(str(directory)) == 1
