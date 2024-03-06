import threading
import webbrowser

import typer
import uvicorn


def open_browser():
    url = "http://localhost:8000/app/"
    webbrowser.open(url, new=0, autoraise=True)


def main():
    timer = threading.Timer(1, open_browser)
    timer.start()

    uvicorn.run(
        "DashAI.back.app_init:app",
        host="127.0.0.1",
        port=8000,
    )


if __name__ == "__main__":
    typer.run(main)
