============
Installation
============

.. image:: https://img.shields.io/pypi/v/dashai.svg
        :target: https://pypi.python.org/pypi/dashai

.. image:: https://readthedocs.org/projects/dashai/badge/?version=latest
        :target: https://dashai.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


DashAI: a graphical toolbox for training, evaluating and deploying state-of-the-art
AI models


Dependencies
============

DashAI requires:

- Python (>= 3.8)
- FastAPI (>= 0.79.0)
- SQLAlchemy (>=1.4.36)
- scikit-learn (>=1.0.2)

Installation
============

You can install DashAI via pip:

.. code:: bash

    $ pip install dashai

Then, to initialize the server and the graphical interface, run:

.. code:: bash

    $ dashai

Finally, go to `http://localhost:3000/ <http://localhost:3000/>`_ in your browser to access to the DashAI graphical interface.


Development
===========


To download and run the development version of DashAI, first, download the repository
and switch to the developing branch: :

.. code:: bash

    $ git clone https://github.com/DashAISoftware/DashAI.git
    $ git checkout staging


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

If you want to launch the front-end test server (without launching the backend) with dummy data, run:

.. code:: bash

    $ yarn json-server

Linting and formatting
~~~~~~~~~~~~~~~~~~~~~~

The project uses as default linter `eslint <https://eslint.org/>`_ with
the `react/recommended`, `standard-with-typescript`` and `prettier`` styles.

To manually run the linter, move to `DashAI/front` and run:

.. code:: bash

    $ yarn eslint src


The project uses `prettier <https://prettier.io/>`_ as default formatter.

To format the code manually, move to `DashAI/front` and execute:

.. code:: bash

    $ yarn prettier --write src


Build the frontend
~~~~~~~~~~~~~~~~~~

Execute from `DashAI/front`:

.. code:: bash

    $ yarn build

Backend
-------


Prepare the environment
~~~~~~~~~~~~~~~~~~~~~~~

First, set the python enviroment using
`conda <https://docs.conda.io/en/latest/miniconda.html>`_:

.. code: bash

    $ conda create -n dashai python=3.10
    $ conda activate dashai

Then, move to `DashAI/back`

.. code:: bash

    $ cd DashAI/back


Later, install the requirements:

.. code:: bash

    $ pip install -r requirements.txt
    $ pip install -r requirements-dev.txt


Running the Backend
~~~~~~~~~~~~~~~~~~~

There are two ways to run DashAI:

1. By executing DashAI as a module:

.. code:: bash

    $ python -c "import DashAI;DashAI.run()"

2. Or,  installing the default build:

.. code:: bash

    $ pip install .
    $ dashai

If you chose the second way, remember to install it each time you make changes.

Make changes on database
~~~~~~~~~~~~~~~~~~~

In case you want to do changes on the database you should do the migrations:

1. First, you need to go to the project root folder if you are not there.

2. Then, create the migration script:

.. code:: bash

    $ alembic revision --autogenerate -m "Describe the changes you did here"

2. And apply migrations:

.. code:: bash

    $ alembic upgrade head

Execute tests
~~~~~~~~~~~~~

DashAI uses `pytest <https://docs.pytest.org/>`_ to perform the backend
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


Linting and formatting
~~~~~~~~~~~~~~~~~~~~~~

The project uses as default backend linter
`ruff <https://github.com/charliermarsh/ruff>`_:

To manually run the linter, move to `DashAI/back` and execute:

.. code:: bash

    $ ruff .


The project uses `black <https://black.readthedocs.io/en/stable/>`_ as default formatter.

To manually format the code, move to `DashAI/back` and execute:

.. code:: bash

    $ black .


Acknowledgments
---------------

This project is sponsored by the `National Center for Artificial Intelligence - CENIA <https://cenia.cl/en/>`_ (FB210017), and the `Millennium Institute for Foundational Data Research - IMFD <https://imfd.cl/en/>`_ (ICN17_002).

The core of the development is carried out by students from the Computer Science Department of the University of Chile and the Federico Santa Maria Technical University.

To see the full list of contributors, visit in `Contributors <https://github.com/DashAISoftware/DashAI/graphs/contributors>`_ the DashAI repository on Github.

.. image:: ./logos.png
   :alt: Collaboration Logos
