============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Bug reports
===========

When `reporting a bug <https://github.com/DashAISoftware/dashAI/issues>`_ please include:

    * Your operating system name and version.
    * The DashAI version (``pip show dashai``) or the commit you are on.
    * Any details about your local setup that might be helpful in troubleshooting.
    * Detailed steps to reproduce the bug.

Documentation improvements
==========================

DashAI could always use more documentation, whether as part of the
official DashAI docs, in docstrings, or even on the web in blog posts,
articles, and such.

Feature requests and feedback
=============================

The best way to send feedback is to file an issue at
https://github.com/DashAISoftware/dashAI/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that code contributions are welcome :)

Development
===========

DashAI uses `uv <https://docs.astral.sh/uv/>`_ to manage the Python environment
and dependencies, and `Yarn <https://yarnpkg.com/>`_ for the frontend.

To set up ``DashAI`` for local development:

1. Fork `DashAI <https://github.com/DashAISoftware/dashAI>`_
   (look for the "Fork" button).

2. Clone your fork locally::

    git clone git@github.com:YOURGITHUBNAME/DashAI.git
    cd DashAI

3. Install the backend and the development dependencies::

    uv sync                 # add --extra cpu on machines without an NVIDIA GPU
    uv run pre-commit install

   If you sync with ``--extra cpu`` (or ``--extra cuda``), pass the same
   ``--extra`` to every ``uv run``; a plain ``uv run`` re-syncs to the default
   torch build.

4. Create a branch for local development::

    git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally. To run the development server::

    uv run python -m DashAI --no-browser --logging-level DEBUG

5. When you're done making changes, run the linter and the test suite::

    uv run ruff check --fix
    uv run ruff format
    uv run pytest tests/

   To run a single test file or a single test::

    uv run pytest tests/back/api/test_components_api.py -v
    uv run pytest tests/back/api/test_components_api.py::test_function_name -v

6. Commit your changes and push your branch to GitHub::

    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website, targeting ``develop``.

Frontend
--------

The frontend lives in ``DashAI/front`` and requires Node LTS and Yarn 3.5.0::

    cd DashAI/front
    yarn install
    yarn start        # dev server on http://localhost:3000
    yarn lint
    yarn test

Pull Request Guidelines
-----------------------

If you need some code review or feedback while you're developing the code just
make the pull request.

For merging, you should:

1. Include passing tests (``uv run pytest tests/``).
2. Make sure the linter is clean (``uv run ruff check``); ``pre-commit`` runs it
   for you on every commit.
3. Update documentation when there's new API, functionality etc.
4. Add a note to ``CHANGELOG.rst`` about the changes.

Tips
----

To run a subset of tests by keyword::

    uv run pytest tests/ -k test_myfeature

To run the tests with a coverage report::

    uv run pytest tests/ --cov=DashAI

Backend tests use an in-memory SQLite database, so no database setup is needed.

To add or remove a dependency (this updates both ``pyproject.toml`` and
``uv.lock``)::

    uv add <package>
    uv remove <package>
