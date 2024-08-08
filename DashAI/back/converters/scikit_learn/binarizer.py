from sklearn.preprocessing import Binarizer as BinarizerOperation

from DashAI.back.core.schema_fields import schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.converters.scikit_learn.sklearn_like_converter import SklearnLikeConverter


class BinarizerSchema(BaseSchema):
     threshold: schema_field(
          float,
          0.0,
          (
               "Feature values below or equal to this are replaced by 0, "
               "above it by 1."
          ),
     )  # type: ignore

class Binarizer(BinarizerOperation, SklearnLikeConverter):
     """Scikit-learn's Binarizer wrapper for DashAI."""

     SCHEMA = BinarizerSchema
     DESCRIPTION = "Binarize data (set feature values to 0 or 1) according to a threshold."