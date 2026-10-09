"""Make the frozen dashAI launcher usable as a Python interpreter.

A PyInstaller bundle ships no ``python`` executable: ``sys.executable`` is the
launcher itself. dashAI installs plugins with ``sys.executable -m pip``, and pip
in turn re-invokes ``sys.executable`` to build isolated wheels, so the launcher
has to honour the two interpreter invocations those paths rely on:

* ``dashAI -m <module> [args...]``   behaves like ``python -m <module> ...``
* ``dashAI <script>.py [args...]``   behaves like ``python <script>.py ...``

Anything else falls through to the normal dashAI CLI.
"""

import runpy
import sys


def _register_distlib_finder():
    """Teach distlib to read its own resources through PyInstaller's loader.

    pip imports pip._vendor.distlib.scripts before it installs a wheel, and
    that module builds its script wrapper table at import time by calling
    distlib.resources.finder(). finder() dispatches on the type of the
    package's loader against a registry that only holds the stdlib loaders and
    zipimporter, so inside a bundle it raises "Unable to locate finder for
    'pip._vendor.distlib'" and every install dies before it starts. Resolution
    is unaffected, since pip imports the module only when it will really
    install something.
    """
    try:
        import pip._vendor.distlib as distlib
        from pip._vendor.distlib.resources import ResourceFinder, register_finder

        # register_finder applies type() to its first argument, so it takes the
        # loader instance and not the loader class.
        register_finder(distlib.__loader__, ResourceFinder)
    except Exception as error:
        print(
            f"dashAI: could not register the distlib resource finder: {error}",
            file=sys.stderr,
        )


def _run_as_interpreter():
    arguments = sys.argv[1:]
    if not arguments:
        return

    _register_distlib_finder()

    if arguments[0] == "-m" and len(arguments) > 1:
        module = arguments[1]
        sys.argv = [sys.argv[0], *arguments[2:]]
        runpy.run_module(module, run_name="__main__", alter_sys=True)
        sys.exit(0)

    if arguments[0].endswith(".py"):
        script = arguments[0]
        sys.argv = [script, *arguments[1:]]
        runpy.run_path(script, run_name="__main__")
        sys.exit(0)


_run_as_interpreter()
