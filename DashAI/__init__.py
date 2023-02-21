# Este archivo corre al hacer import DashAI
import os
import signal
import time
import webbrowser
from subprocess import Popen


def run():
    url = "http://localhost:3000/"

    procs = [
        Popen(
            "python -m DashAI.back.main",
            shell=True,
        ),
        Popen(
            "python -m http.server -d DashAI/front/build 3000",
            shell=True,
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
