# flake8: noqa


def load_model(path):
    """Load a model exported from DashAI (a ``.dashai-model`` file).

    Imported lazily so ``import DashAI`` stays cheap and never starts the app.
    Warning: loading a package runs pickled code; only load trusted files.
    """
    from DashAI.back.model_package.load import load_model as _load_model

    return _load_model(path)
