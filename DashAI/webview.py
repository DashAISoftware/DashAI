import multiprocessing

import typer

from DashAI.__main__ import main

if __name__ == "__main__":
    # In frozen builds (PyInstaller), multiprocessing children re-execute this
    # entry point with bootstrap argv (--multiprocessing-fork / -c ...);
    # freeze_support() must run before any app code so those children are
    # diverted into the worker bootstrap instead of starting a second app.
    # No-op when running under a regular interpreter.
    multiprocessing.freeze_support()
    typer.run(lambda: main(webview=True))
