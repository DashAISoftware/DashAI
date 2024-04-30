import os
import pathlib
import subprocess
from subprocess import Popen


def init_dev():
    """
    Main function to start the dashai application.

    This only works if the PATH environment variable has python as
    the python 3.8 executable.
    """
    venv_name = "env"
    local_path = pathlib.Path("~/.DashAI").expanduser()
    venv_path = os.path.join(local_path, venv_name)

    if not os.path.exists(local_path):
        os.mkdir(local_path)

    if not os.path.exists(venv_path):
        subprocess.run(["python", "-m", "venv", venv_path])

    scripts_path = os.path.join(venv_path, "Scripts")  # ~/.DashAI/venv/Scripts
    pip_path = os.path.join(scripts_path, "pip")

    subprocess.run([pip_path, "install", "-r", "requirements.txt"])
    subprocess.run([pip_path, "install", "-r", "requirements-dev.txt"])

    # Command to open terminal and run the commands
    full_command = "start cmd /c "

    actual_path = pathlib.Path(__file__).parent.absolute()
    front_path = pathlib.Path(actual_path, "DashAI/front")

    # Command to start the front
    yarn_command = full_command + f"yarn --cwd {front_path} start"

    # Command to start the backend
    python_command = (
        full_command + f"{os.path.join(scripts_path, 'python.exe')} -m DashAI"
    )

    try:
        # Execute the command to start the front
        Popen(yarn_command, shell=True)

        # Execute the command to start the backend
        Popen(python_command, shell=True)

    except KeyboardInterrupt:
        pass


init_dev()
