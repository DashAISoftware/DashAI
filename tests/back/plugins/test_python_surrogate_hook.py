"""Tests for the PyInstaller runtime hook that lets the launcher act as python.

Plugins are installed with ``sys.executable -m pip``, which in a frozen build
means running the dashAI launcher itself, so the hook has to keep honouring the
two interpreter invocations pip relies on.
"""

import json
import pathlib
import runpy
import sys

import pytest

HOOK_PATH = (
    pathlib.Path(__file__).resolve().parents[3] / "hooks" / "rthook_python_surrogate.py"
)


def _run_hook():
    runpy.run_path(str(HOOK_PATH), run_name="dashai_surrogate_hook")


def test_hook_file_exists():
    assert HOOK_PATH.is_file()


def test_hook_runs_a_module_like_dash_m(tmp_path, monkeypatch, capsys):
    (tmp_path / "surrogate_probe.py").write_text(
        "import sys\nprint('module ran', sys.argv[1:])\n", encoding="utf-8"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(sys, "argv", ["dashAI", "-m", "surrogate_probe", "--flag"])

    with pytest.raises(SystemExit) as exit_info:
        _run_hook()

    assert exit_info.value.code == 0
    assert "module ran ['--flag']" in capsys.readouterr().out


def test_hook_runs_a_script_path(tmp_path, monkeypatch):
    marker = tmp_path / "argv.json"
    script = tmp_path / "in_process.py"
    script.write_text(
        "import json, pathlib, sys\n"
        f"pathlib.Path(r'{marker}').write_text(json.dumps(sys.argv))\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["dashAI", str(script), "build_wheel"])

    with pytest.raises(SystemExit) as exit_info:
        _run_hook()

    assert exit_info.value.code == 0
    assert json.loads(marker.read_text()) == [str(script), "build_wheel"]


def test_hook_ignores_the_regular_dashai_cli(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["dashAI", "--no-browser", "-ll", "DEBUG"])

    _run_hook()

    assert sys.argv == ["dashAI", "--no-browser", "-ll", "DEBUG"]


def test_hook_ignores_an_empty_command_line(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["dashAI"])

    _run_hook()

    assert sys.argv == ["dashAI"]


def test_hook_ignores_a_bare_dash_m(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["dashAI", "-m"])

    _run_hook()

    assert sys.argv == ["dashAI", "-m"]


def test_hook_registers_distlib_by_loader_instance(monkeypatch):
    """distlib's register_finder applies type() itself, so it needs the instance.

    Passing the loader class instead registers ``type`` and leaves the real
    loader unmapped, which is what made every install inside the bundle fail
    with "Unable to locate finder for 'pip._vendor.distlib'".
    """
    import pip._vendor.distlib as distlib
    from pip._vendor.distlib import resources

    class FakeFrozenLoader:
        pass

    monkeypatch.setattr(sys, "argv", ["dashAI"])
    namespace = runpy.run_path(str(HOOK_PATH), run_name="dashai_surrogate_hook")

    monkeypatch.setattr(distlib, "__loader__", FakeFrozenLoader(), raising=False)
    monkeypatch.setitem(resources._finder_registry, FakeFrozenLoader, None)

    namespace["_register_distlib_finder"]()

    assert resources._finder_registry[FakeFrozenLoader] is resources.ResourceFinder


def test_hook_survives_a_missing_distlib(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["dashAI"])
    namespace = runpy.run_path(str(HOOK_PATH), run_name="dashai_surrogate_hook")
    monkeypatch.setitem(sys.modules, "pip._vendor.distlib", None)

    namespace["_register_distlib_finder"]()

    assert "could not register the distlib resource finder" in capsys.readouterr().err
