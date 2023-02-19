Changelog
=========

0.0.5 - TODO: Add date here.
----------------------------


Change several module, class and function names to fulfill pep8 naming convention guidelines:

- change file names to snake_case.
- rename `TaskLib` to `task`.
- move `TaskLib/task` to `task`.
- rename `Models` to `models`.

Reorganize the repository modules using as basis the following coockiecutters:

- Fullstack FastAPI: https://github.com/tiangolo/full-stack-fastapi-postgresql
- Pypackage: https://github.com/audreyfeldroy/cookiecutter-pypackage
- pylibrary: https://github.com/ionelmc/cookiecutter-pylibrary

Changes associated with the above: 

- added a `pyproject.toml` with configurations to black, isort and ruff.
- move tests from `DashAI/back/test` to `tests/`.
- move database connection (`bd.py`) to `DashAI/back/db/session.py`.
- moved `requirements.txt` and `requirements-dev.txt` to the project root.
- added python .gitignore from github gitignore repo (https://github.com/github/gitignore/blob/main/Python.gitignore).
- added github issue template (generated using `cookiecutter-pypackage`).
- include a contributing guidelines (generated `cookiecutter-pylibrary`).
- added a changelog (generated using `cookiecutter-pylibrary`).
- added `flake8`, `black`, `isort`, `ruff`, `sphinx`, `sphinx_rtd_theme` to requirements-dev.txt.
- delete requirements from `docs/`.

Other changes:

- updated outdated requirements (`fastapi`, `sqlalchemy`, `scikit-learn`, `joblib`, `numpy`).
- translate README to rst.
- update pytest github action to run the tests from the root.
