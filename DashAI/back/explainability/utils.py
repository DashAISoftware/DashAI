import logging

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy import exc
from sqlalchemy.orm import Session

from DashAI.back.api.deps import get_db
from DashAI.back.core.config import component_registry
from DashAI.back.database.models import Run

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

# TODO: Evaluar qué funciones son comunes entre métodos de 
# una misma clase para ordenarlas.

def load_predictor(db: Session = Depends(get_db), run_id: int):
    try:
        run: Run = db.get(Run, run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
            )
    except exc.SQLAlchemyError as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal database error",
        ) from e
    
    run_path = run.run_path
    model = component_registry[run.model_name]["class"]
    predictor = model.load(run_path)

    return predictor