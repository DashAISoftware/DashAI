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
