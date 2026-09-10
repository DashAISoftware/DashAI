from typing import TYPE_CHECKING, Final, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon
from DashAI.back.types.dashai_data_type import DashAIDataType

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class FeatureSelectionConverter(BaseConverter):
    """Base class for converters that select a subset of features from the dataset.

    Feature selection converters remove low-relevance columns based on
    statistical tests, thresholds, or rankings. Examples include SelectKBest,
    SelectPercentile, GenericUnivariateSelect, SelectFDR, SelectFPR, and
    SelectFWE.

    Use these converters to reduce overfitting, speed up training, and improve
    model interpretability by retaining only the most informative features.

    These converters only drop columns; the retained columns keep their
    original values untouched, so their data types must be preserved instead of
    being coerced to float.
    """

    CATEGORY = MultilingualString(
        en="Feature Selection",
        es="Selección de Características",
        pt="Seleção de Características",
        de="Merkmalsauswahl",
        zh="特征选择",
    )
    ICON: Final[str] = Icon.FilterList.value
    COLOR: Final[str] = "rgb(255, 206, 86)"

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "FeatureSelectionConverter":
        """Fit the selector while remembering the input column types.

        Feature selection only keeps a subset of the input columns without
        modifying their values, so the original types are captured here to be
        returned later by ``get_output_type``. Types are recorded during ``fit``
        (rather than ``transform``) because scikit-learn auto-wraps ``transform``
        on subclasses and would coerce its output back to a pandas DataFrame.

        Parameters
        ----------
        x : DashAIDataset
            The input dataset to fit the selector on.
        y : DashAIDataset, optional
            Target values for the supervised selectors. Defaults to None.

        Returns
        -------
        FeatureSelectionConverter
            The fitted selector instance (self).
        """
        if hasattr(x, "types") and x.types is not None:
            self._input_types = dict(x.types)
        return super().fit(x, y)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the original DashAI data type of a retained column.

        Since feature selection leaves the retained columns' values unchanged,
        the output type matches the input type of that column.

        Parameters
        ----------
        column_name : str, optional
            The name of the retained column. Defaults to None.

        Returns
        -------
        DashAIDataType
            The original type of the column. Falls back to ``float64`` when the
            input type is unknown (feature selectors only operate on numbers).
        """
        input_types = getattr(self, "_input_types", None)
        if input_types is not None and column_name in input_types:
            return input_types[column_name]

        import pyarrow as pa

        from DashAI.back.types.value_types import Float

        return Float(arrow_type=pa.float64())
