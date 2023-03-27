======
DashAI
======

.. image:: https://img.shields.io/pypi/v/dashai.svg
        :target: https://pypi.python.org/pypi/dashai

.. image:: https://readthedocs.org/projects/dashai/badge/?version=latest
        :target: https://dashai.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


DashAI: a graphical toolbox for training, evaluating and deploying state-of-the-art AI models


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

Then, to initialize the server and the graphical interface, execute:

.. code:: bash

    $ dashai

Finally, go to `http://localhost:3000/ <http://localhost:3000/>` in your browser to access to the DashAI graphical interface.


Development
===========

To download and run the development version of DashAI, first, download the repository and switch to the developing branch: : 

.. code:: bash

    $ git clone https://github.com/DashAISoftware/DashAI.git
    $ git checkout staging

Then, set the python enviroment (using for example, conda) 

.. code: bash

    $ conda create -n dashai python=3.10
    $ conda activate dashai 

and install the requirements: 

.. code:: bash

    $ pip install -r requirements.txt
    $ pip install -r requirements-dev.txt


Build the frontend
------------------

Install node and npm. Then, go to DashAI/front:

.. code:: bash

    $ cd DashAI/front

and run:

.. code:: bash

    $ npm run build

Running DashAI
--------------

There are two ways to run DashAI:

.. code:: bash

    $ python -c "import DashAI;DashAI.run()"

or

.. code:: bash

    $ pip install .
    $ dashai

If you chose the second way, remember to install it each time you make changes.
