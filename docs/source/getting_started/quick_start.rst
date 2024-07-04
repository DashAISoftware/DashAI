.. _quick_start:

Quick Start
=========================

In this section we show how to get **DashAI** and use it to solve a simple task.

Quick installation (Pypi)
-------------------------


DashAI needs Python 3.8 or greater to be installed. Once that requirement is satisfied, you can install DashAI via pip:

.. code:: bash

    $ pip install dashai

Then, to initialize the server and the graphical interface, run:

.. code:: bash

    $ dashai

Finally, go to `http://localhost:3000/ <http://localhost:3000/>`_ in your browser to access to the DashAI graphical interface.


First Experiment
----------------

To perform an experiment in **DashAI** (i.e., train a machine learning model) you need three pieces: a *dataset*, a *task*, and a *model*.

* Select a dataset from `here <https://github.com/DashAISoftware/DashAI_Datasets>`_.
* Explain the task we want to solve, i.e., tabular classification, inputs and outputs.

Dataset
^^^^^^^

* The selected dataset sets the dataloader to use.
* Load it and assign it a name
* Explain a little bit the dataset summary

Task
^^^^

* Select the task and set the name of the experiment
* Use default columns

Model
^^^^^

* Select two models, SVC and DummyClassifier.
* Save the experiment

Now we have the three pieces we need to perform the experiment, so we need to run the experiment and wait for it to finish.

Results
^^^^^^^

* Go to the experiment and select the results icon.
* View the global summary
* Go to SVM results
