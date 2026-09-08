============
dashAI
============

.. image:: https://img.shields.io/pypi/v/dashai.svg
        :target: https://pypi.python.org/pypi/dashai

.. image:: https://readthedocs.org/projects/dashai/badge/?version=latest
        :target: https://docs.dash-ai.com/
        :alt: Documentation Status


A graphical toolbox for training, evaluating and deploying state-of-the-art
AI models

.. image:: ./images/dashai-logo.svg
   :alt: dashAI Logo

Requirements
============

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * -
     - Desktop installers
     - PyPI / source install
   * - **Operating system**
     - Windows 10/11 x64, macOS 14+ on Apple Silicon (no Intel Mac build),
       Linux x64 with glibc 2.35 or newer and FUSE 2
     - Windows, macOS or Linux x64
   * - **CPU**
     - x86_64 **with AVX2** (Intel Haswell 2013+, AMD Excavator / Zen+), or
       Apple Silicon
     - x86_64 or Apple Silicon, AVX2 not required
   * - **Python**
     - Nothing to install: the installers bundle their own Python 3.12
     - You install it yourself: Python 3.10 or greater (3.12 recommended)

Desktop installers (Windows / macOS / Linux)
=============================================

The easiest way to get started. Desktop installers, ready to use, are
published with every release. They are **CPU only** and bundle everything you
need, so no Python or extra setup is required.

Download the file for your system from the
`latest release <https://github.com/DashAISoftware/DashAI/releases/latest>`_:

* **Windows (x64):** ``dashAI-<version>-x64-windows.exe``
* **macOS (Apple Silicon):** ``dashAI-<version>-arm-osx.dmg``
* **Linux (x64):** ``dashAI-<version>-x64-linux.AppImage``

On Windows and macOS, run the installer, launch dashAI, and the graphical
interface opens automatically.

On Linux, make the AppImage executable and run it:

.. code:: bash

    $ chmod +x dashAI-<version>-x64-linux.AppImage
    $ ./dashAI-<version>-x64-linux.AppImage

The AppImage bundles its own Python, so nothing needs to be installed. It
requires glibc 2.35 or newer (Ubuntu 22.04+, Debian 12+, Fedora 36+, and most
distributions from 2022 on) and FUSE 2 to mount. If FUSE is missing, run it
with ``./dashAI-<version>-x64-linux.AppImage --appimage-extract-and-run``.

When double clicked, the AppImage opens a terminal window to show the server
logs. This needs a terminal emulator, which every standard desktop (GNOME, KDE,
XFCE, and others) already provides, so no setup is required. On a minimal system
with no terminal emulator the log window is skipped, but the app still starts
and opens the browser as usual.

**Note:** the desktop installers ship with CPU only PyTorch and
``llama-cpp-python``. For NVIDIA (CUDA) or AMD (ROCm) GPU acceleration, use the
pip installation below.

**Note:** the installers need a CPU with AVX2 (Intel 2013+, AMD Excavator /
Zen+). The bundled native libraries, PyTorch and the ``libggml`` shipped inside
``llama-cpp-python``, are built for it, and on older hardware whichever one is
imported first kills the process with ``Illegal instruction``. Clone the
repository and install from source instead, which pulls wheels that run on
older CPUs (it may still fail if the CPU is very old, but it is worth trying).


Installation (PyPI)
===================

dashAI needs Python 3.10 or greater. We strongly recommend installing it inside
an isolated environment to avoid clashes with other packages. The quickest way
to do that is with `uv <https://docs.astral.sh/uv/getting-started/installation/>`_
(recommended, it even installs Python for you); classic ``venv``/``conda`` with
``pip`` works exactly the same if you prefer it.

**Shortcut:** if you just want dashAI as an app with the default PyTorch build
for your platform, uv can install it in its own isolated environment and put
the ``dashai`` command on your PATH in one line:

.. code:: bash

    $ uv tool install dashai

For GPU acceleration, a CPU-slim install, or LLM (GGUF) support, follow the
steps below instead.

Installing dashAI also installs PyTorch with the default build for your
platform, which works out of the box on CPU. To enable GPU acceleration (NVIDIA
CUDA or AMD ROCm), or to force a CPU only build, reinstall PyTorch from the
matching index as shown in step 3. ``llama-cpp-python`` is required to run LLM
models (GGUF / Llama, Mistral, Qwen, and similar) inside the app, but it is
never installed automatically, so install it in step 3 if you need those models.


1. Create an environment
-------------------------

**Any OS (uv, recommended)**

.. code:: bash

    $ uv venv --python 3.12
    $ source .venv/bin/activate          # Windows: .venv\Scripts\activate

**Linux / macOS (venv)**

.. code:: bash

    $ python3 -m venv .venv
    $ source .venv/bin/activate

**Windows (venv, PowerShell)**

.. code:: powershell

    > python -m venv .venv
    > .venv\Scripts\Activate.ps1

**Any OS (conda)**

.. code:: bash

    $ conda create -n dashai python=3.12
    $ conda activate dashai


2. Install dashAI
-----------------

With the environment active:

.. code:: bash

    $ uv pip install dashai

    # or, with plain pip:
    $ pip install dashai


3. Select a PyTorch build and (optional) llama-cpp
--------------------------------------------------

This step is optional on CPU (step 2 already installed a working PyTorch).
Run the section below that matches your hardware to pick a specific build.

Every ``pip install`` command below can also be run as ``uv pip install`` with
the same flags: same result, just faster.

CPU only (Linux / macOS / Windows)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On Linux the default PyTorch ships the large CUDA build; reinstall from the CPU
index if you want a smaller CPU only install:

.. code:: bash

    $ pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --force-reinstall --no-cache-dir

    # Optional, for GGUF / Llama models (precompiled CPU wheel, no build tools):
    $ pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu --force-reinstall --no-cache-dir

NVIDIA GPU (CUDA 12.8)
~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    # Torch CUDA 12.8 (prebuilt wheels)
    $ pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128 --force-reinstall --no-cache-dir

    # Llama compiled with CUDA offload (requires build tools, see below)
    $ pip install llama-cpp-python -C cmake.args="-DGGML_CUDA=on" --force-reinstall --no-cache-dir --verbose

AMD GPU (ROCm 6.4)
~~~~~~~~~~~~~~~~~~

.. code:: bash

    # Torch ROCm (prebuilt wheels)
    $ pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm6.4 --force-reinstall --no-cache-dir

    # Llama compiled with HIP/ROCm offload (requires build tools, see below)
    $ pip install llama-cpp-python -C cmake.args="-DGGML_HIP=on" --force-reinstall --no-cache-dir --verbose


Build tools for GPU llama-cpp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``-C cmake.args=...`` commands above compile ``llama-cpp-python`` from
source. They require:

* `CMake <https://cmake.org/>`_ (required to drive the build)
* A C compiler:

  * **Linux:** ``gcc`` or ``clang``
  * **Windows:** Visual Studio (C++ build tools / MSVC) or MinGW
  * **macOS:** Xcode

* **NVIDIA (CUDA):** NVIDIA drivers and the NVIDIA CUDA Toolkit. Use version
  ``>=12.8`` for RTX 5000 series GPUs to work.
* **AMD (ROCm):** the ROCm / HIP SDK and AMD drivers.

If you want to skip compilation, precompiled ``llama-cpp-python`` wheels are
available for CPU and CUDA:

.. code:: bash

    $ pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu --force-reinstall --no-cache-dir
    $ pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/<cuda-version> --force-reinstall --no-cache-dir

Replace ``<cuda-version>`` with your CUDA tag. Prebuilt wheels are published for
``cu118``, ``cu121``, ``cu122``, ``cu123``, ``cu124``, ``cu125``, ``cu130`` and
``cu132`` (for example ``cu124``). See the
`llama-cpp-python installation docs <https://llama-cpp-python.readthedocs.io/en/latest/>`_
for the available wheels and other backend options.


4. Run dashAI
-------------

Start the server and graphical interface with:

.. code:: bash

    $ dashai

Then open `http://localhost:8000/ <http://localhost:8000/>`_ in your browser to
access the dashAI graphical interface.


Docker
======

dashAI can also run inside a container. Two Dockerfiles are provided at the
repository root.

CPU image
---------

``Dockerfile`` builds a CPU only image (CPU PyTorch). Build and run it with:

.. code:: bash

    $ docker build -t dashai .
    $ docker run -p 8000:8000 dashai

NVIDIA GPU image (CUDA)
-----------------------

``Dockerfile.cuda`` builds a CUDA enabled image (CUDA 12.8 PyTorch and
``llama-cpp-python`` compiled with CUDA offload). Build and run it with:

.. code:: bash

    $ docker build -t dashai:cuda -f Dockerfile.cuda .
    $ docker run --gpus all -p 8000:8000 dashai:cuda

Then open `http://localhost:8000/ <http://localhost:8000/>`_ in your browser.

To pass the host GPU into the container with ``--gpus all`` you need the NVIDIA
drivers plus the runtime that wires the GPU into Docker. How you get that
runtime depends on your setup:

* **Native Linux Docker:** install the
  `NVIDIA Container Toolkit <https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html>`_
  on the host.
* **Docker Desktop (Windows / macOS):** the GPU runtime is bundled with the
  WSL 2 backend, so you only install the NVIDIA driver on Windows and enable the
  WSL 2 backend. See the
  `Docker Desktop GPU docs <https://docs.docker.com/desktop/features/gpu/>`_.
* **Docker Engine inside a WSL 2 distro (without Docker Desktop):** install the
  NVIDIA Container Toolkit inside the WSL distro, following the
  `CUDA on WSL guide <https://docs.nvidia.com/cuda/wsl-user-guide/index.html>`_.


Test datasets
=============

Some datasets you can use to try dashAI are available `here <https://github.com/DashAISoftware/DashAI_Datasets>`_.


Development
===========


To download and run the development version of dashAI, first, download the repository
and switch to the developing branch:

.. code:: bash

    $ git clone https://github.com/DashAISoftware/DashAI.git
    $ git checkout develop


Frontend
--------

.. warning::

    All commands executed in this section must be run
    from `DashAI/front`. To move there, run:

    .. code::

        $ cd DashAI/front


Prepare the environment
~~~~~~~~~~~~~~~~~~~~~~~

1. `Install the LTS node version <https://nodejs.org/en>`_.

2. Install `Yarn` package manager following the instructions located on the
   `yarn getting started <https://yarnpkg.com/getting-started>`_ page.

3. Move to `DashAI/front` and Install the project packages
   using yarn:

.. code:: bash

    $ cd DashAI/front
    $ yarn install


Running the frontend
~~~~~~~~~~~~~~~~~~~~~~

Move to DashAI/front if you are not on that route:

.. code:: bash

    $ cd DashAI/front

Then, launch the front-end development server by running the following command:

.. code:: bash

    $ yarn start


Backend
-------


Prepare the environment
~~~~~~~~~~~~~~~~~~~~~~~

Dependencies are managed with `uv <https://docs.astral.sh/uv/>`_. Install it
following the `official instructions <https://docs.astral.sh/uv/getting-started/installation/>`_,
then install the project (uv creates the virtualenv, installs the package in
editable mode and all development dependencies):

.. code:: bash

    $ uv sync
    $ uv run pre-commit install

On machines without an NVIDIA GPU you can use the much lighter CPU-only
PyTorch wheels instead:

.. code:: bash

    $ uv sync --extra cpu

On NVIDIA machines, the ``cuda`` extra pins the CUDA 12.8 PyTorch wheels. To
also get LLM (GGUF) support with CUDA offload, set ``CMAKE_ARGS`` so that
``llama-cpp-python`` compiles against CUDA (this requires CMake, a C compiler
and the CUDA toolkit; see "Build tools for GPU llama-cpp" above):

.. code:: bash

    $ uv cache clean llama-cpp-python
    $ CMAKE_ARGS="-DGGML_CUDA=on" uv sync --extra cuda --reinstall-package llama-cpp-python

The first command and the ``--reinstall-package`` flag matter: uv skips
packages that are already installed and caches built wheels, and neither
check looks at ``CMAKE_ARGS``, so without them a previous CPU build gets
silently reused. Without ``CMAKE_ARGS``, ``llama-cpp-python`` still installs
but runs on CPU (there is no prebuilt CUDA wheel on PyPI). If nvcc rejects
your default gcc as too new, point it at an older one you have installed,
for example ``CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_CUDA_HOST_COMPILER=/usr/bin/g++-13"``.

If you prefer plain ``pip``, the same setup works inside any environment
(``venv`` or ``conda``) since all metadata lives in ``pyproject.toml``. Note
that this skips the lockfile, so versions may differ slightly from the ones
the team and CI use:

.. code:: bash

    $ pip install -e . --group dev    # --group needs pip >= 25.1
    $ pre-commit install

Running the Backend
~~~~~~~~~~~~~~~~~~~

There are two ways to run dashAI from the root of the repository:

.. code:: bash

    $ uv run python -m DashAI

Or, through the installed entry point:

.. code:: bash

    $ uv run dashai

**Important:** if you synced with an extra, pass the same extra to ``uv run``
(for example ``uv run --extra cpu python -m DashAI``). A plain ``uv run``
re-syncs the environment to the default set and swaps your PyTorch build back
to the PyPI one.

(If you installed with pip inside your own environment, drop the ``uv run``
prefix: ``python -m DashAI`` or ``dashai``.)


Optional Flags
==============

**Setting the local execution path**

With the `--local-path` (alias `-lp`) option you can determine where dashAI will save its local
files, such as datasets, experiments, runs and others.
The following example shows how to set the folder in the local `.DashAI` directory:

.. code:: bash

    $ python -m DashAI --local-path "~/.DashAI"


**Setting the logging level**

Through the `--logging-level` (alias `-ll`) parameter, you can set which logging level the dashAI
backend server will have.

.. code:: bash

    $ python -m DashAI --logging-level INFO

The possible levels available are: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

Note that the `--logging-level` not only affects the dashAI loggers, but also
the datasets (which is set to the same level as dashAI) and the
SQLAlchemy (which is only activated when logging level is DEBUG).


**Disabling automatic browser opening**

By default, dashAI will open a browser window pointing to the application
after starting. If you prefer to disable this behavior, you can use the
`--no-browser` (alias `-nb`) flag:

.. code:: bash

    $ python -m DashAI --no-browser


**Checking Available Options**

You can check all available options through the command:

.. code:: bash

    $ python -m DashAI --help


Database Migrations
===================

Migrations are managed through `Alembic <https://alembic.sqlalchemy.org/en/latest/>`_.

They are automatically executed when starting dashAI. However, if you want to
run them manually, you can do so using the following command (inside the
`DashAI/` folder):

.. code-block:: bash

    $ alembic upgrade head

This command applies all pending migrations up to the latest revision.

---

Creating a New Migration
------------------------

After modifying the database models, a new migration can be generated using:

.. code-block:: bash

    $ alembic revision --autogenerate -m "<<Your message here>>"

Where ``<<Your message here>>`` is a brief description of the changes introduced
(e.g., *add model metadata table*, *update dataset schema*).

Generated migrations are located in the ``alembic/versions`` directory and
**must be committed to the repository**.

It is strongly recommended to review the autogenerated migration file before
applying it, as Alembic may not always detect complex changes correctly.

---

Applying Migrations
-------------------

To apply all pending migrations:

.. code-block:: bash

    $ alembic upgrade head

To upgrade to a specific revision:

.. code-block:: bash

    $ alembic upgrade <revision_id>

---

Downgrading Migrations
----------------------

If you need to revert database changes, migrations can be downgraded using:

.. code-block:: bash

    $ alembic downgrade -1

This command reverts the last applied migration.

To downgrade to a specific revision:

.. code-block:: bash

    $ alembic downgrade <revision_id>

---

Checking Migration Status
-------------------------

To view the current migration applied to the database:

.. code-block:: bash

    $ alembic current

To list the full migration history:

.. code-block:: bash

    $ alembic history

---


Testing
=======

Execute tests
-------------

dashAI uses `pytest <https://docs.pytest.org/>`_ to perform the backend
tests.
To execute the backend tests

1. Move to `DashAI/back`

.. code:: bash

    $ cd DashAI/back

2. Run:

.. code:: bash

    $ pytest tests/

.. note::

    The database session is parametrized in every endpoint as
    ``db: Session = Depends(get_db)`` so we can test endpoints on a test database
    without making changes to the main database.



Acknowledgments
===============

.. INSTITUTIONS-BLOCK:START

.. This block is auto-generated from docs/static/institutions/institutions.json.
   Edit that file and run ``python scripts/render_institutions.py``. Do not edit by hand.

This project is developed in collaboration with:

* `University of Chile <https://uchile.cl/>`_ - Leading Institution
* `Fcfm <https://www.fcfm.uchile.cl/>`_ - Leading Institution
* `CENIA <https://www.cenia.cl/>`_ - Associated Institution
* `IMFD <https://imfd.cl/en/>`_ - Collaborator
* `Unholster <https://unholster.com/>`_ - Industry Partner

Supported by ANID through Fondef IDEA ID25I10330, Fondef VIU23P 0110, and grants supporting the centers CENIA (FB210017) and IMFD (ICN17_002). Developed by students of DCC UChile and UTFSM.

.. image:: images/logos.png
   :alt: Logos of collaborating institutions

.. INSTITUTIONS-BLOCK:END

To see the full list of contributors, visit in `Contributors <https://github.com/DashAISoftware/DashAI/graphs/contributors>`_ the dashAI repository on Github.
