import logging
from typing import List

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


def validate_inputs_outputs(
    names: List[str],
    inputs: List[str],
    outputs: List[str],
) -> None:
    """Validate the columns to be chosen as input and output.
    The algorithm considers those that already exist in the dataset.
    Parameters
    ----------
    names : List[str]
        Dataset column names.
    inputs : List[str]
        List of input column names.
    outputs : List[str]
        List of output column names.
    """
    if len(inputs) + len(outputs) > len(names):
        raise ValueError(
            "Inputs and outputs cannot have more elements than names. "
            f"Number of inputs: {len(inputs)}, "
            f"number of outputs: {len(outputs)}, "
            f"number of names: {len(names)}. "
        )
        # Validate that inputs and outputs only contain elements that exist in names
    if not set(names).issuperset(set(inputs + outputs)):
        raise ValueError(
            "Inputs and outputs can only contain elements that exist in names."
        )
        # Validate that the union of inputs and outputs is equal to names
    if set(inputs + outputs) != set(names):
        raise ValueError(
            "The union of the elements of inputs and outputs list must be equal to "
            "elements in the list of names."
        )
