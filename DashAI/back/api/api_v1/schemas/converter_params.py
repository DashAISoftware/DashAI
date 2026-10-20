from typing import Any, Dict, List, Union

from pydantic import BaseModel


class ConverterParams(BaseModel):
    order: int = 0
    params: Dict[str, Any] = None
    scope: Dict[str, Union[List[int], List[Dict[str, Any]]]] = None
    target: Union[Dict[str, Any], None] = None

    def serialize(self) -> Dict[str, Any]:
        return {
            "order": self.order,
            "params": self.params,
            "scope": self.scope,
            "target": self.target,
        }


class ConverterParams(BaseModel):
    notebook_id: int
    converter: str
    parameters: ConverterParams
