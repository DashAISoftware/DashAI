#!/usr/bin/env python

# Esto corre el __init__.py ubicado en la carpeta DashAI
# Este archivo corre al hacer import DashAI
import os
import signal
import time
import webbrowser
from subprocess import Popen

from DashAI import run


def run():

    url = "http://localhost:3000/"

    procs = [
        Popen(
            "python main.py",
            shell=True,
            cwd=os.path.join(os.path.dirname(os.path.realpath(__file__)), "back"),
        ),
        Popen(
            "python -m http.server 3000",
            shell=True,
            cwd=os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "front/build"
            ),
        ),
    ]

    def handler(signum, frame):
        print("\nShutting down DashAI")
        for p in procs:
            p.terminate()
        time.sleep(2)
        # TODO Maybe close the window on SIGINT

    signal.signal(signal.SIGINT, handler)
    time.sleep(1)
    webbrowser.open(url, new=0, autoraise=True)

    for p in procs:
        p.wait()


if __name__ == "__main__":
    run()
