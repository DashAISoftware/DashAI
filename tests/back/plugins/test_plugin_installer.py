import json
import os
import pathlib
import subprocess
import sys
from typing import Iterable, Tuple
from unittest.mock import Mock, patch

import pytest

from DashAI.back.plugins import installer
from DashAI.back.plugins.installer import (
    PluginInstallError,
    canonical_name,
    install_requirement,
    pip_command,
    read_ledger,
    resolve_missing_distributions,
    uninstall_requirement,
)


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


INTERPRETER_DIR = f"py{sys.version_info.major}.{sys.version_info.minor}"


@pytest.fixture
def plugins_dir(tmp_path, monkeypatch) -> pathlib.Path:
    monkeypatch.setenv("DASHAI_LOCAL_PATH", str(tmp_path))
    directory = tmp_path / "plugins" / INTERPRETER_DIR
    directory.mkdir(parents=True)
    return directory


def _completed(returncode: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(
        args=["pip"], returncode=returncode, stdout=stdout, stderr=stderr
    )


def _report(*distributions: Tuple[str, str, str]) -> dict:
    return {
        "version": "1",
        "install": [
            {
                "metadata": {"name": name, "version": version},
                "download_info": {"url": url},
            }
            for name, version, url in distributions
        ],
    }


def _write_fake_distribution(
    directory: pathlib.Path,
    name: str,
    version: str = "1.0.0",
    files: Iterable[str] = ("dummy_pkg/__init__.py",),
    extra_record_lines: Iterable[str] = (),
) -> pathlib.Path:
    dist_info = directory / f"{name.replace('-', '_')}-{version}.dist-info"
    dist_info.mkdir(parents=True)
    records = []
    for relative in files:
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")
        records.append(f"{relative},sha256=x,0")
    records.extend(extra_record_lines)
    records.append(f"{dist_info.name}/METADATA,sha256=x,0")
    records.append(f"{dist_info.name}/RECORD,,")
    (dist_info / "RECORD").write_text("\n".join(records), encoding="utf-8")
    (dist_info / "METADATA").write_text(
        f"Name: {name}\nVersion: {version}\n", encoding="utf-8"
    )
    return dist_info


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("DashAI-Frankenstein", "dashai-frankenstein"),
        ("dashai_frankenstein", "dashai-frankenstein"),
        ("dashai.frankenstein", "dashai-frankenstein"),
        ("  DashAI__Plugin  ", "dashai-plugin"),
    ],
)
def test_canonical_name(raw, expected):
    assert canonical_name(raw) == expected


def test_pip_command_targets_the_interpreter_running_dashai():
    assert pip_command() == [sys.executable, "-m", "pip"]


def test_pip_command_fails_when_pip_is_missing():
    with patch("importlib.util.find_spec", return_value=None):  # noqa: SIM117
        with pytest.raises(PluginInstallError, match="pip is not available"):
            pip_command()


def test_pip_environment_exposes_the_plugins_directory(plugins_dir, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "/elsewhere")
    monkeypatch.setenv("PIP_USER", "1")
    monkeypatch.setenv("PIP_TARGET", "/somewhere")

    environment = installer._pip_environment(plugins_dir)

    assert environment["PYTHONPATH"].split(os.pathsep) == [
        str(plugins_dir),
        "/elsewhere",
    ]
    assert environment["PIP_USER"] == "0"
    assert environment["PIP_REQUIRE_VIRTUALENV"] == "0"
    assert "PIP_TARGET" not in environment


def test_run_pip_raises_with_the_error_lines(plugins_dir):
    failure = _completed(returncode=1, stderr="noise\nERROR: no such package\n")

    with patch("subprocess.run", return_value=failure):  # noqa: SIM117
        with pytest.raises(PluginInstallError, match="ERROR: no such package"):
            installer._run_pip(["install", "nope"], plugins_dir)


PIP_CRASH_STDERR = "\n".join(
    [
        "ERROR: Exception:",
        "Traceback (most recent call last):",
        '  File "pip/_vendor/distlib/resources.py", line 346, in finder',
        "    raise DistlibException(...)",
        "DistlibException: Unable to locate finder for 'pip._vendor.distlib'",
    ]
)


def test_run_pip_keeps_the_traceback_after_an_error_line(plugins_dir):
    """pip reports a crash as an ERROR line plus the traceback explaining it."""
    failure = _completed(
        returncode=2,
        stdout="Collecting dashai-plugin",
        stderr=PIP_CRASH_STDERR,
    )

    with patch("subprocess.run", return_value=failure):  # noqa: SIM117
        with pytest.raises(PluginInstallError) as error_info:
            installer._run_pip(["install", "dashai-plugin"], plugins_dir)

    message = str(error_info.value)
    assert message.startswith("ERROR: Exception:")
    assert "Unable to locate finder" in message
    assert "Traceback (most recent call last):" in message


def test_run_pip_caps_the_reported_output(plugins_dir):
    noise = "\n".join(f"line {index}" for index in range(200))
    failure = _completed(returncode=2, stderr=f"ERROR: boom\n{noise}")

    with patch("subprocess.run", return_value=failure):  # noqa: SIM117
        with pytest.raises(PluginInstallError) as error_info:
            installer._run_pip(["install", "dashai-plugin"], plugins_dir)

    reported = str(error_info.value).splitlines()
    assert len(reported) == installer._PIP_ERROR_CONTEXT_LINES


def test_run_pip_reports_a_silent_failure(plugins_dir):
    with (
        patch("subprocess.run", return_value=_completed(returncode=9)),
        pytest.raises(PluginInstallError, match="pip exited with code 9"),
    ):
        installer._run_pip(["install", "dashai-plugin"], plugins_dir)


def test_run_pip_falls_back_to_the_output_tail(plugins_dir):
    failure = _completed(returncode=2, stderr="something went wrong")

    with patch("subprocess.run", return_value=failure):  # noqa: SIM117
        with pytest.raises(PluginInstallError, match="something went wrong"):
            installer._run_pip(["install", "nope"], plugins_dir)


def test_resolve_missing_distributions_reads_the_pip_report(plugins_dir):
    report = _report(
        ("DashAI_Frankenstein", "1.2.0", "https://files/dashai_frankenstein.whl"),
        ("frankenstein-transformer", "1.1.0", "https://files/transformer.whl"),
    )

    def fake_run_pip(arguments, directory):
        pathlib.Path(arguments[arguments.index("--report") + 1]).write_text(
            json.dumps(report), encoding="utf-8"
        )
        return _completed()

    with patch.object(installer, "_run_pip", side_effect=fake_run_pip) as run_pip:
        distributions = resolve_missing_distributions(
            "dashai-frankenstein", plugins_dir
        )

    arguments = run_pip.call_args.args[0]
    assert arguments[:2] == ["install", "--dry-run"]
    assert "--target" not in arguments
    assert arguments[-1] == "dashai-frankenstein"
    assert distributions == [
        {
            "name": "dashai-frankenstein",
            "version": "1.2.0",
            "url": "https://files/dashai_frankenstein.whl",
        },
        {
            "name": "frankenstein-transformer",
            "version": "1.1.0",
            "url": "https://files/transformer.whl",
        },
    ]


def test_resolve_missing_distributions_ignores_incomplete_entries(plugins_dir):
    report = {"install": [{"metadata": {"name": "broken"}}, {"download_info": {}}]}

    def fake_run_pip(arguments, directory):
        pathlib.Path(arguments[arguments.index("--report") + 1]).write_text(
            json.dumps(report), encoding="utf-8"
        )
        return _completed()

    with patch.object(installer, "_run_pip", side_effect=fake_run_pip):
        assert resolve_missing_distributions("broken", plugins_dir) == []


def test_install_requirement_only_installs_the_missing_distributions(plugins_dir):
    distributions = [
        {"name": "dashai-plugin", "version": "1.0", "url": "https://files/plugin.whl"},
        {"name": "extra-dep", "version": "2.0", "url": "https://files/extra.whl"},
    ]

    with (
        patch.object(
            installer, "resolve_missing_distributions", return_value=distributions
        ),
        patch.object(installer, "_run_pip", return_value=_completed()) as run_pip,
    ):
        installed = install_requirement("DashAI-Plugin")

    assert installed == ["dashai-plugin", "extra-dep"]
    arguments = run_pip.call_args.args[0]
    assert "--no-deps" in arguments
    assert arguments[arguments.index("--target") + 1] == str(plugins_dir)
    assert arguments[-2:] == ["https://files/plugin.whl", "https://files/extra.whl"]
    assert read_ledger(plugins_dir) == {"dashai-plugin": ["dashai-plugin", "extra-dep"]}


def test_install_requirement_is_a_no_op_when_already_satisfied(plugins_dir):
    with (
        patch.object(installer, "resolve_missing_distributions", return_value=[]),
        patch.object(installer, "_run_pip") as run_pip,
    ):
        assert install_requirement("dashai-plugin") == []

    run_pip.assert_not_called()


def test_uninstall_requirement_removes_the_recorded_files(plugins_dir):
    _write_fake_distribution(
        plugins_dir, "dashai-plugin", files=("dashai_plugin/__init__.py",)
    )
    installer._write_ledger(plugins_dir, {"dashai-plugin": ["dashai-plugin"]})

    removed = uninstall_requirement("DashAI-Plugin")

    assert removed == ["dashai-plugin"]
    assert not (plugins_dir / "dashai_plugin").exists()
    assert list(plugins_dir.glob("*.dist-info")) == []
    assert read_ledger(plugins_dir) == {}


def test_uninstall_requirement_keeps_dependencies_other_plugins_need(plugins_dir):
    _write_fake_distribution(
        plugins_dir, "dashai-plugin", files=("dashai_plugin/__init__.py",)
    )
    _write_fake_distribution(plugins_dir, "shared-dep", files=("shared_dep/core.py",))
    installer._write_ledger(
        plugins_dir,
        {
            "dashai-plugin": ["dashai-plugin", "shared-dep"],
            "dashai-other": ["shared-dep"],
        },
    )

    removed = uninstall_requirement("dashai-plugin")

    assert removed == ["dashai-plugin"]
    assert (plugins_dir / "shared_dep" / "core.py").exists()
    assert read_ledger(plugins_dir) == {"dashai-other": ["shared-dep"]}


def test_uninstall_requirement_ignores_records_outside_the_plugins_directory(
    plugins_dir,
):
    escapee = plugins_dir.parent / "escapee.txt"
    escapee.write_text("keep me", encoding="utf-8")
    _write_fake_distribution(
        plugins_dir,
        "dashai-plugin",
        files=("dashai_plugin/__init__.py",),
        extra_record_lines=("../escapee.txt,sha256=x,0",),
    )
    installer._write_ledger(plugins_dir, {"dashai-plugin": ["dashai-plugin"]})

    uninstall_requirement("dashai-plugin")

    assert escapee.exists()


def test_uninstall_requirement_removes_console_scripts(plugins_dir):
    """Wheels record scripts as ../../bin/name, which --target puts in bin/."""
    script = plugins_dir / "bin" / "plugin-cli.exe"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    _write_fake_distribution(
        plugins_dir,
        "dashai-plugin",
        files=("dashai_plugin/__init__.py",),
        extra_record_lines=("../../bin/plugin-cli.exe,sha256=x,0",),
    )
    installer._write_ledger(plugins_dir, {"dashai-plugin": ["dashai-plugin"]})

    uninstall_requirement("dashai-plugin")

    assert not script.exists()


@pytest.mark.parametrize(
    ("relative", "expected"),
    [
        ("dashai_plugin/__init__.py", "dashai_plugin/__init__.py"),
        ("../../bin/plugin-cli.exe", "bin/plugin-cli.exe"),
        (r"..\..\Scripts\plugin.exe", "Scripts/plugin.exe"),
    ],
)
def test_resolve_record_entry_stays_inside_the_plugins_directory(
    plugins_dir, relative, expected
):
    resolved = installer._resolve_record_entry(plugins_dir, relative)

    assert resolved == (plugins_dir / expected).resolve()


def test_resolve_record_entry_rejects_entries_it_cannot_place(plugins_dir):
    assert installer._resolve_record_entry(plugins_dir, "../..") is None


def test_uninstall_requirement_falls_back_to_the_environment(plugins_dir):
    with patch.object(installer, "_run_pip", return_value=_completed()) as run_pip:
        assert uninstall_requirement("dashai-legacy") == []

    assert run_pip.call_args.args[0] == [
        "uninstall",
        "-y",
        "--disable-pip-version-check",
        "dashai-legacy",
    ]


def test_uninstall_requirement_survives_a_failed_environment_removal(plugins_dir):
    with patch.object(
        installer, "_run_pip", side_effect=PluginInstallError("not installed")
    ):
        assert uninstall_requirement("dashai-legacy") == []


def test_read_ledger_tolerates_a_corrupted_file(plugins_dir):
    (plugins_dir / installer.LEDGER_FILENAME).write_text("{oops", encoding="utf-8")

    assert read_ledger(plugins_dir) == {}


def test_read_ledger_normalizes_plugin_names(plugins_dir):
    (plugins_dir / installer.LEDGER_FILENAME).write_text(
        json.dumps({"version": 1, "plugins": {"DashAI_Plugin": ["Some_Dep"]}}),
        encoding="utf-8",
    )

    assert read_ledger(plugins_dir) == {"dashai-plugin": ["Some_Dep"]}


def test_install_requirement_reports_pip_failures(plugins_dir):
    with (
        patch.object(
            installer,
            "resolve_missing_distributions",
            side_effect=PluginInstallError("ERROR: no matching distribution"),
        ),
        pytest.raises(PluginInstallError, match="no matching distribution"),
    ):
        install_requirement("dashai-missing")


def test_find_distribution_directory_matches_canonical_names(plugins_dir):
    dist_info = _write_fake_distribution(plugins_dir, "DashAI.Weird_Name")

    found = installer._find_distribution_directory(plugins_dir, "dashai-weird-name")

    assert found == dist_info


def test_remove_distribution_returns_false_when_not_installed(plugins_dir):
    assert installer._remove_distribution(plugins_dir, "absent") is False


def test_get_installed_plugins_directory_does_not_create_it(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHAI_LOCAL_PATH", str(tmp_path / "fresh"))

    directory = installer.get_installed_plugins_directory()

    assert not directory.exists()


def test_run_pip_uses_the_plugins_environment(plugins_dir):
    with patch("subprocess.run", return_value=_completed()) as run:
        installer._run_pip(["install", "anything"], plugins_dir)

    assert run.call_args.args[0][:3] == [sys.executable, "-m", "pip"]
    assert str(plugins_dir) in run.call_args.kwargs["env"]["PYTHONPATH"]


def test_install_requirement_activates_the_plugins_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHAI_LOCAL_PATH", str(tmp_path))
    monkeypatch.delenv("PYTHONPATH", raising=False)

    with patch.object(installer, "resolve_missing_distributions", return_value=[]):
        install_requirement("dashai-plugin")

    directory = installer.get_installed_plugins_directory()
    assert directory.is_dir()
    assert str(directory) in sys.path


def test_ledger_round_trip(plugins_dir):
    installer._write_ledger(plugins_dir, {"a": ["b"]})

    assert read_ledger(plugins_dir) == {"a": ["b"]}


def test_uninstall_requirement_defaults_to_the_plugin_name(plugins_dir):
    _write_fake_distribution(plugins_dir, "dashai-plugin")

    assert uninstall_requirement("dashai-plugin") == ["dashai-plugin"]


def test_resolve_missing_distributions_reports_unreadable_reports(plugins_dir):
    with patch.object(installer, "_run_pip", return_value=Mock()):  # noqa: SIM117
        with pytest.raises(PluginInstallError, match="resolution report"):
            resolve_missing_distributions("dashai-plugin", plugins_dir)
