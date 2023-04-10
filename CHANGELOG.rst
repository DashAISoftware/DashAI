Changelog
=========

0.0.12
------

- Added frontend development documentation.
- improved backend development documentation.
- Change front package management to yarn.
- Improved gitignore for frontend.
- Added missing packages that allow the front end to run locally
- Added prettier as default frontend formatter for the project.
- Formatted all front end files according to prettier styles.
- Changed navbar to a MUI responsive implementation.
- Fix fronend router and links.
- Add design colors to MUI theme provider.
- Moved route handling to App.jsx
- Change page container to MUI container component. 
- The experiment table and new experiment button is now implemented using MUI's 
  Datagrid and Button. Its styles and design were also improved.
- Moved the experiments API to its own module in `src/api/experiments`. Is by default typed.
- ExperimentsTable component now imports these methods and executes them in an asynchronous wrapper inside the component.
- Interactivity is added through snackbars/toast and loading animations. These can be seen when the getExperiments request fails and when an experiment is deleted (correctly or incorrectly).
- Typescript is enabled on the front end.
- Interfaces are declared for the main application objects: Experiment, Dataset and Run. These can be found in the `src/types`` folder.


0.0.11
------

**Main change**: Dataset endpoints
New dataset endpoints on `DashAI/back/api_v1` follow the RESTful api paradigm

Changes
*******

- Implemented put and delete on datasets
- Implemented get on /dataset/ and /dataset/id
- Now all datasets raise HTTPException if an error occurs.
- Fixed docstring styling

0.0.10
------

**Main change**: Legacy Endpoints
Enabled again some endpoints that have been purged after the repository changes.
We added multiple api versions and fixed frontend to work with the new api structure.

Changes
*******

- Added api_v0 and api_v1
- Legacy endpoints are implemented in `DashAI/back/api/api_v0/endpoints/old_endpoints.py`
- Fixed some bugs on dataloaders typing
- Fixed a bug on `DashAI/back/dataloaders/classes/dataloader.py` when splitting and given test and train sizes to train_test_split method (float sum error)

- Changed .env file to point new endpoints
- Fixed react navigate from '/...' to '/app/...'

0.0.9
-----

**Main change**: Merged ModelInstance and Run in one table

Changes
*******

- Base was refactored to database/models, so fixed import in init
- Merged the ModelInstance table with the Run table

0.0.8
-----

**Main change**: Serving from FastAPI
Remove a secondary server to serve our front end. Also, it enhances GitHub workflow to build the frontend and then run pytest.

Fixed some .gitignore redundancies

Changes
*******

- Unified pytest and npm test to a single workflow with two jobs
- pytest job uses the react build generated on the npm cli cycle.
- Removed the secondary process that ran the server on python's http.server
- DashAI/back/database/db.py
- Fixed deprecated import in SQLAlchemy 2.0
- Enabled frontend serve and static files on FastAPI
- Renamed app path from / to /app
- Renamed api path from / to /api
- Added database health check on execution.
- Renamed a bunch of paths from images/* to /images/*
- Renamed NavBar's paths from /* to /app/*

0.0.7
-----

**Main change**: Database model
Cleaned database model.

Changes
*******

- We are now using the modern version of SQLAlchemy Mapped syntax
- We have 4 tables now: Dataset, Experiment, Model and Run
- Dataset One-to-Many Experiment
- Experiment One-to-Many Model
- Model One-to-One Run
- Model and Run cascades on deletion.
- Added states for the future state machine.

0.0.6
-----

The main goal was to enable database and dataloaders.

This purged most of old database and endpoint work, because it needs to be reconsidered. Only most basic endpoints such as dataset upload and dataset database are online.

**This will break most of frontend usability and endpoints. It is really important to reconsider how the calls are made, which endpoints are necessary and what parameters are given to the backend**

Changes
*******

- Database name is now DashAI.sqlite from dashAI.sqlite
- Merged with last PR "Change execution working directory, meet pep8 and update project structure"
- Renamed session back to db because of the call `db.session.query...` was `session.session.query...`
- Removed previous example_datasets that wont work with the new dataloaders. Next dataloaders PR will contain new CSV and JSON example datasets.
- main.py was purged of most endpoints.
- Frontend shouldn't need an endpoint to check if api is online. Removed /info.

Routing
********

`back/routers/`

- Created routers to decrease main.py complexity
- Now dataset endpoint follow RESTful structure
- experiment route is a placeholder. Expermients need to be reconsidered with an orchestrator.

`back/dataloaders/classes`

- Implemented multiple dataloaders from the abstract class DataLoader, where each dataloader should implement load\_data method
- DataLoader is responsible for split\_dataset and set\_classes

Dataloaders
***********

`back/dataloaders/dataloader_schemas` & `back/dataloaders/params_schema`
- These jsons contain information that is shown on the frontend. Maybe on next iteration switch them to python dictionaries
- Translation is outdated


0.0.5 
-----

**Main change**: Move execution default working directories to the root folder. 

This change is intended to standardize the execution and import paths of the entire application by having the project root as the default path. 
This includes changing the back and front execution scripts (Popen) of the

- backend from `DashAI/back/main`  to `python -m DashAI.back.main`.
- frontend from `DashAI/front/build` to `python -m http.server -d DashAI/front/build 3000`.

See more of this change in `DashAI/__init__.py`

Furthermore, every python import was changed to absolute imports, using commonly the following pattern: 
`from DashAI.back.some_module import some_class`. 

**Pep8**

Change several modules, classes and function names to fulfill pep8 naming convention guidelines:

- change file names to snake_case.
- rename `TaskLib` to `task`.
- move `TaskLib/task` to `task`.
- rename `Models` to `models`.


**Project structure**

Reorganize the repository modules using as basis the following coockiecutters:

- Fullstack FastAPI: https://github.com/tiangolo/full-stack-fastapi-postgresql
- Pypackage: https://github.com/audreyfeldroy/cookiecutter-pypackage
- pylibrary: https://github.com/ionelmc/cookiecutter-pylibrary

Changes associated with the coockiecutters suggestions: 

- added a `pyproject.toml` with configurations to black, isort and ruff.
- move tests from `DashAI/back/test` to `tests/`.
- move database connection (`bd.py`) to `DashAI/back/db/session.py`.
- moved `requirements.txt` and `requirements-dev.txt` to the project root.
- added python .gitignore from github gitignore repo (https://github.com/github/gitignore/blob/main/Python.gitignore).
- added github issue template (generated using `cookiecutter-pypackage`).
- include a contributing guidelines (generated `cookiecutter-pylibrary`).
- added a changelog (generated using `cookiecutter-pylibrary`).
- added `flake8`, `black`, `isort`, `ruff`, `sphinx`, `sphinx_rtd_theme`, `httpx`, `Flake8-pyproject` and `sqlalchemy-stubs` to requirements-dev.txt.
- delete requirements from `docs/`.

**Other minor changes**

- updated outdated requirements (`fastapi`, `sqlalchemy`, `scikit-learn`, `joblib`, `numpy`).
- fix minimum requirements in `requirements.txt` to run the tests in github actions (and hopefully also when installing the package in a newly created environment).
- translate README to rst.
- update pytest github action to run the tests from the root.
- added `if __name__ == "__main__":` condition to `dashai` file to prevent server execution when some test is running.
- implemented a test to check if the backend server is running.
- rename `NumericalClassification` to `TabularClassification`, both in tasks and models.

**Registries**

- changed `Task` to `BaseTask`.
- changed `Model` to `BaseModel`.
- added a `_compatible_tasks` abstract attribue to each class that extends `BaseModel`.
- implemented `BaseRegistry`, a class that is capable to store a register any component of Dash with a minimum amount of configuration.
- implemented `TaskComponentMappingMixin` a mixin that allows each component registered in a generic registry to also be linked to its compatible tasks through a mapping dict.
- implemented `TaskRegistry`, a `BaseRegistry` class whose object is intended to register dash task.
- implemented `ModelRegistry`, a `BaseRegistry` class whose object is intended to register dash model.
- added a `task_registry` and `model_registry` objects to main application.
