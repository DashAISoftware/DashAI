import os
import pathlib
import subprocess
from subprocess import Popen


def init_dev():
    """
    Función principal para iniciar la aplicación dashai.
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

    # Comando para abrir terminal y correr el comandos
    full_command = "start cmd /c "

    actual_path = pathlib.Path(__file__).parent.absolute()
    front_path = pathlib.Path(actual_path, "DashAI/front")

    # Comando para ejecutar yarn
    yarn_command = full_command + f"yarn --cwd {front_path} start"

    # Comando para ejecutar el backend
    python_command = (
        full_command + f"{os.path.join(scripts_path, 'python.exe')} -m DashAI"
    )

    try:
        # Ejecutar el comando para iniciar el front
        Popen(yarn_command, shell=True)

        # Ejecutar el comando para iniciar el backend
        Popen(python_command, shell=True)

    except KeyboardInterrupt:
        pass


init_dev()
