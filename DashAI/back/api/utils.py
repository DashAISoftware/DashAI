import logging

import pydantic
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import HTTPException

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


def parse_params(model_class, params):
    """
    Parse JSON from string to pydantic model.

    Parameters
    ----------
    model_class : BaseModel
        Pydantic model to parse.
    params : str
        Stringified JSON with parameters.

    Returns
    -------
    BaseModel
        Pydantic model parsed from Stringified JSON.
    """
    try:
        model_instance = model_class.model_validate_json(params)
        return model_instance
    except pydantic.ValidationError as e:
        log.error(e)
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        ) from e


def parse_string_to_list(string):
    """
    Parse a string to a list.
    """
    import re

    no_brackets = re.sub(r"[\[\]\(\)\{\}]", "", string)
    no_double_quotes = re.sub(r'"', "", no_brackets)
    no_quotes = re.sub(r"'", "", no_double_quotes)
    splitted_and_stripped = [item.strip() for item in no_quotes.split(",")]
    return splitted_and_stripped


def parse_string_to_dict(string):
    """
    Parse a string to a dictionary.
    """
    import ast

    return ast.literal_eval(string)


def cast_string_to_type(string):
    """
    Cast a string to a type.
    """
    import numpy as np
    import pandas as pd

    type_map = {
        "int": int,
        "int32": np.int32,
        "int64": np.int64,
        "float32": np.float32,
        "float64": np.float64,
        "np.nan": np.nan,
        "pandas.NA": pd.NA,
    }
    return type_map.get(string, string)


def create_random_state():
    """
    Create a random state using numpy random.
    """
    import numpy as np

    return np.random.RandomState()


def remove_path(path):
    """Removes a file or directory

    Parameters
    ----------
    path : str
        The path to the file or directory to remove.

    Raises
    ------
    ValueError
        Raised if the path is not a file, directory, or symbolic link.
    """
    import os
    import shutil

    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
    else:
        raise ValueError("file {} is not a file or dir.".format(path))
