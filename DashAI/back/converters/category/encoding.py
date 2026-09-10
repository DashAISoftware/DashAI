from typing import TYPE_CHECKING, Final, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class EncodingConverter(BaseConverter):
    """Base class for converters that encode categorical features into numeric form.

    Encoding converters transform non-numeric columns into a representation
    that machine learning models can process. Examples include OneHotEncoder,
    OrdinalEncoder, and LabelEncoder.

    Use these converters when the dataset contains string or categorical columns
    that must be converted before model training.

    The ``transform`` method appends encoded columns (``encoded_<col>``) to the
    dataset instead of replacing the originals, so the source column is always
    preserved.
    """

    CATEGORY = MultilingualString(
        en="Encoding", es="Codificación", pt="Codificação", de="Kodierung", zh="编码"
    )
    ICON: Final[str] = Icon.Dns.value
    COLOR: Final[str] = "rgb(138, 43, 226)"
    PREFIX: str = "encoded_"

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Encode ``x`` and append the result as new ``encoded_*`` columns.

        Calls the underlying sklearn transformer (via ``SklearnWrapper.transform``)
        to produce encoded values, then renames every output column to
        ``encoded_<col>`` and appends them to the original dataset. The original
        scope columns are left unchanged.

        Parameters
        ----------
        x : DashAIDataset
            The dataset to transform (contains only the scope columns).
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            Dataset with the original scope columns preserved plus new
            ``encoded_*`` columns appended.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        encoded = super().transform(x, y)

        combined_table = x.arrow_table
        combined_types = dict(x.types)

        for col in encoded.column_names:
            prefixed = f"{self.PREFIX}{col}"
            combined_table = combined_table.append_column(
                prefixed, encoded.arrow_table[col]
            )
            combined_types[prefixed] = encoded.types[col]

        return DashAIDataset(combined_table, types=combined_types, splits=x.splits)
