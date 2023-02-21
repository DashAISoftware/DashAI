Changelog
=========

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
- translate README to rst.
- update pytest github action to run the tests from the root.
- added `if __name__ == "__main__":` condition to `dashai` file to prevent server execution when some test is running.
- implemented a test to check if the backend server is running.
- rename `NumericalClassification` to `TabularClassification`, both in tasks and models.