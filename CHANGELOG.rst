Changelog
=========

0.0.6 24/02/2023
----------------

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


0.0.5 - TODO: Add date here.
----------------------------

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
- added a `_compatible_tasks` abstract attribue to `BaseModel`.
- implemented `TaskRegistry`, object that registers all the tasks that could be used when executing dash (either from the package or plugins).
- implemented `ModelRegistry`, object that registers all the models that could be used when executing dash (either from the package or plugins).
- added a `task_registry` and `model_registry` to main application.
- added a metaclass `TaskMetaClass` to `BaseTask` that allows each Task (that extends BaseTask) to hold an empty `compatible_models` list that is not shared with the others tasks.

- TODO:getitem, and contains for model_registry, repr for model_registry and task_registry.
- more testing.