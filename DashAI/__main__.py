"""Main module for DashAI package.

Contains the main function that is executed when the package is called from the
command line.
"""

import logging
import multiprocessing
import os
import pathlib
import signal
import subprocess
import sys
import threading
import warnings
import webbrowser
from contextlib import suppress

import typer
from typing_extensions import Annotated

from DashAI.back.core.enums.logging_levels import LoggingLevel

# Suppress noisy third-party startup warnings
warnings.filterwarnings(
    "ignore",
    message=".*mediapipe.*",
    category=UserWarning,
    module="controlnet_aux",
)
warnings.filterwarnings(
    "ignore",
    message=".*Importing from timm.models.layers.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*Importing from timm.models.registry.*",
    category=FutureWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*Overwriting tiny_vit.*",
    category=UserWarning,
    module="controlnet_aux",
)
warnings.filterwarnings(
    "ignore",
    message=".*found in sys.modules after import.*",
    category=RuntimeWarning,
)


def _print_banner() -> None:
    print()
    print("  ╔═══════════════════════════════════════════════════════╗")
    print("  ║                                                       ║")
    print("  ║   ██████╗   █████╗  ███████╗ ██╗  ██╗  █████╗  ██╗    ║")
    print("  ║   ██╔══██╗ ██╔══██╗ ██╔════╝ ██║  ██║ ██╔══██╗ ██║    ║")
    print("  ║   ██║  ██║ ███████║ ███████╗ ███████║ ███████║ ██║    ║")
    print("  ║   ██║  ██║ ██╔══██║ ╚════██║ ██╔══██║ ██╔══██║ ██║    ║")
    print("  ║   ██████╔╝ ██║  ██║ ███████║ ██║  ██║ ██║  ██║ ██║    ║")
    print("  ║   ╚═════╝  ╚═╝  ╚═╝ ╚══════╝ ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═╝    ║")
    print("  ║                                                       ║")
    print("  ║   Loading application, please wait...                 ║")
    print("  ║                                                       ║")
    print("  ╚═══════════════════════════════════════════════════════╝")
    print()


def open_browser() -> None:
    _wait_for_backend_server(timeout=1200)
    url = "http://localhost:8000/app/"
    webbrowser.open(url=url, new=0, autoraise=True)


def _start_huey_thread() -> threading.Thread:
    from huey.bin.huey_consumer import consumer_main

    def dummy_signal(signalnum, handler):
        return None

    signal.signal = dummy_signal

    sys.argv = [
        "huey_consumer",
        "DashAI.back.dependencies.job_queues.huey_job_queue.huey",
        "--delay",
        "0.1",
        "--backoff",
        "1",
    ]

    t = threading.Thread(target=consumer_main, daemon=True)
    t.start()
    return t


def _start_backend_server(
    local_path: pathlib.Path, logging_level: LoggingLevel
) -> None:
    import uvicorn

    from DashAI.back.app import create_app

    app = create_app(
        local_path=local_path,
        logging_level=logging_level.value,
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Uvicorn server on http://127.0.0.1:8000")

    uvicorn.run(
        app=app,
        host=os.environ.get("DASHAI_HOST", "127.0.0.1"),
        port=8000,
    )


def _wait_for_backend_server(host="127.0.0.1", port=8000, timeout=15):
    """Wait for the backend server to start by attempting to connect to the specified
    host and port."""
    import socket
    import time

    timeout = 1000
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.5)
    return False


def _start_webview(local_path: pathlib.Path, logger: logging.Logger) -> None:
    import base64

    import webview

    class DownloadApi:
        """Exposed to JavaScript via window.pywebview.api for native file saving."""

        def save_file(self, filename: str, data_b64: str) -> bool:
            try:
                result = window.create_file_dialog(
                    webview.SAVE_DIALOG,
                    save_filename=filename,
                )
                if result:
                    filepath = result if isinstance(result, str) else result[0]
                    with open(filepath, "wb") as f:
                        f.write(base64.b64decode(data_b64))
                    logger.info(f"File saved: {filepath}")
                    return True
            except Exception:
                logger.exception("Failed to save file")
            return False

    api = DownloadApi()
    window = webview.create_window(
        "dashAI", "http://127.0.0.1:8000", hidden=True, js_api=api
    )

    _DOWNLOAD_INTERCEPT_JS = """
    (function() {
        if (window.__dashaiDownloadHandler) return;
        window.__dashaiDownloadHandler = true;

        function handleDownload(url, filename) {
            fetch(url)
                .then(function(r) { return r.blob(); })
                .then(function(blob) {
                    var reader = new FileReader();
                    reader.onload = function() {
                        var b64 = reader.result.split(',')[1];
                        window.pywebview.api.save_file(filename, b64);
                    };
                    reader.readAsDataURL(blob);
                })
                .catch(function(err) {
                    console.error('DashAI download intercept failed:', err);
                });
        }

        // Intercept programmatic .click() on <a download>
        var origClick = HTMLAnchorElement.prototype.click;
        HTMLAnchorElement.prototype.click = function() {
            if (this.hasAttribute('download')) {
                handleDownload(this.href, this.download || 'download');
                return;
            }
            return origClick.call(this);
        };

        // Intercept user clicks on <a download> (e.g. tour sample dataset link)
        document.addEventListener('click', function(e) {
            var link = e.target.closest('a[download]');
            if (link) {
                e.preventDefault();
                e.stopPropagation();
                handleDownload(link.href, link.download || 'download');
            }
        }, true);
    })();
    """

    def _inject_download_handler():
        try:
            window.evaluate_js(_DOWNLOAD_INTERCEPT_JS)
            logger.info("Download intercept JS injected.")
        except Exception:
            logger.exception("Failed to inject download handler JS")

    window.events.loaded += _inject_download_handler

    def load_logic():
        if _wait_for_backend_server(timeout=120):
            logger.info("Backend server is up. Loading webview.")
            window.load_url("http://127.0.0.1:8000/app/")
            window.show()
        else:
            logger.error("Failed to connect to backend server. Timeout.")
            window.destroy()

    # create cache directory for webview (if doesn't exist)
    cache_dir = local_path / "web_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    webview.start(load_logic, private_mode=False, storage_path=str(cache_dir))


def main(
    local_path: Annotated[
        pathlib.Path,
        typer.Option(
            "--local-path",
            "-lp",
            help="Path where dashAI files will be stored.",
        ),
    ] = "~/.DashAI",  # type: ignore
    logging_level: Annotated[
        LoggingLevel,
        typer.Option(
            "--logging-level",
            "-ll",
            help=(
                "dashAI App Logging level. "
                "Only in DEBUG mode, SQLAlchemy logging is enabled."
            ),
        ),
    ] = LoggingLevel.INFO,
    no_browser: Annotated[
        bool,
        typer.Option(
            "--no-browser",
            "-nb",
            help="Run without automatically opening the browser.",
            is_flag=True,
        ),
    ] = False,
    webview: Annotated[
        bool,
        typer.Option(
            "--window-mode",
            "-wm",
            help="Run in windowed mode (using webview).",
            is_flag=True,
        ),
    ] = False,
) -> None:
    _print_banner()
    logging.getLogger(name=__package__).setLevel(level=logging_level.value)
    logger = logging.getLogger(__name__)
    logger.info("Starting dashAI application.")
    huey_process = None

    resolved_local = pathlib.Path(local_path).expanduser().absolute()
    os.environ["DASHAI_LOCAL_PATH"] = str(resolved_local)
    os.environ["DASHAI_LOGGING_LEVEL"] = logging_level.value

    # Installed plugins live outside the app environment, so put their
    # directory on PYTHONPATH before copying the environment for the Huey
    # consumer: the consumer imports plugin components too.
    from DashAI.back.plugins.environment import activate_plugins_directory

    activate_plugins_directory(resolved_local)

    child_env = os.environ.copy()

    logger.info("Starting Huey consumer.")

    # In a PyInstaller bundle or an AppImage, sys.executable is the bundled
    # launcher (not a bare Python), so spawning the Huey consumer as
    # "sys.executable -m huey..." re-enters the app instead of running Python.
    # Run it in a thread in those cases.
    in_appimage = bool(os.environ.get("APPIMAGE") or os.environ.get("APPDIR"))
    if getattr(sys, "frozen", False) or in_appimage:
        logger.info("Running inside a bundled launcher (PyInstaller/AppImage).")
        _start_huey_thread()
        logger.info("Started embedded Huey consumer (thread).")
    else:
        logger.info("Running in development mode.")

        huey_cmd = [
            sys.executable,
            "-m",
            "huey.bin.huey_consumer",
            "DashAI.back.dependencies.job_queues.huey_job_queue.huey",
            "--delay",
            "0.1",
            "--backoff",
            "1",
        ]
        huey_process = subprocess.Popen(huey_cmd, env=child_env)
        logger.info(f"Started external Huey consumer (PID: {huey_process.pid})")

    try:
        if webview:
            logger.info("Creating FastAPI application...")

            t = threading.Thread(
                target=_start_backend_server,
                args=(resolved_local, logging_level),
                daemon=True,
            )
            t.start()

            _start_webview(local_path=resolved_local, logger=logger)
        else:
            if not no_browser:
                logger.info("Opening browser.")
                timer = threading.Timer(interval=1, function=open_browser)
                timer.start()
            else:
                logger.info("Browser auto-open disabled (--no-browser/-nb).")

            _start_backend_server(
                local_path=resolved_local, logging_level=logging_level
            )

    finally:
        if huey_process:
            logger.info(f"Terminating Huey consumer (PID: {huey_process.pid})")
            with suppress(Exception):
                huey_process.terminate()
                huey_process.wait(timeout=5)


def run():
    typer.run(main)


if __name__ == "__main__":
    # In frozen builds (PyInstaller), multiprocessing children re-execute this
    # entry point with bootstrap argv (--multiprocessing-fork / -c ...);
    # freeze_support() must run before any app code so those children are
    # diverted into the worker bootstrap instead of starting a second app.
    # No-op when running under a regular interpreter.
    multiprocessing.freeze_support()
    typer.run(main)
