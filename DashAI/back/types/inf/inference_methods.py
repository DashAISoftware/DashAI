import pandas as pd

import DashAI.back.types.inf.ptype.Machine as Machine
from DashAI.back.types.date_utils import detect_date_format
from DashAI.back.types.inf.Inference import InferenceMethod
from DashAI.back.types.inf.ptype.Machines import MACHINES, Machines
from DashAI.back.types.inf.ptype.PtypeCat import PtypeCat
from DashAI.back.types.utils import PTYPE_TO_DASHAI


class DashAIPtype(PtypeCat, InferenceMethod):
    """
    A class to represent a DashAI Ptype inference method.

    This class extends the InferenceMethod and PtypeCat classes to provide
    functionality for inferring types in DashAI applications.

    Parameters
    ----------
    cat_threshold : float
        Probability threshold for categorical classification.
        Default is 0.7 (stricter than before).
    max_unique_ratio : float
        Maximum ratio of unique values for categorical detection.
    max_unique_count : int
        Maximum number of unique categories allowed.
    """

    def __init__(
        self,
        cat_threshold: float = 0.7,
        max_unique_ratio: float = 0.05,
        max_unique_count: int = 50,
    ):
        super().__init__(
            cat_threshold=cat_threshold,
            max_unique_ratio=max_unique_ratio,
            max_unique_count=max_unique_count,
        )
        self.types.extend(["time", "float_comma"])

        current_machines = {
            **MACHINES,
            "time": Machine.Time(),
            "float_comma": Machine.FloatComma(),
        }

        self.machines = Machines(self.types, current_machines)

    def infer_types(self, data) -> dict:
        """
        Infers types from the provided data using the PtypeCat model.

        Parameters
        ----------
        data : pd.DataFrame
            The input data for type inference.

        Returns
        -------
        dict
            A dictionary mapping column names to inferred types.
        """
        schema = self.schema_fit(data)

        inferred_types = {}
        for col_name, col_object in schema.cols.items():
            ptype_type = col_object.inferred_type()

            # Map ptype type to DashAI type
            if ptype_type in PTYPE_TO_DASHAI:
                dashai_info = PTYPE_TO_DASHAI[ptype_type].copy()
            else:
                # Fallback to text for unknown types
                dashai_info = {"type": "Text", "dtype": "string"}

            # Handle categorical specially
            # include categories and preserve original dtype
            if ptype_type == "categorical":
                unique_vals = col_object.get_normal_values()
                dashai_info["categories"] = unique_vals

                # Preserve original dtype from pandas DataFrame
                original_dtype = data[col_name].dtype
                if pd.api.types.is_integer_dtype(original_dtype):
                    dashai_info["dtype"] = "int64"
                elif pd.api.types.is_float_dtype(original_dtype):
                    dashai_info["dtype"] = "float64"
                elif pd.api.types.is_bool_dtype(original_dtype):
                    dashai_info["dtype"] = "bool"
                else:
                    dashai_info["dtype"] = "string"

                # Infer encoder from dtype
                if dashai_info["dtype"] in ("int64", "float64"):
                    dashai_info["encoder"] = "label"
                else:
                    dashai_info["encoder"] = "one_hot"

            # A Date column stores a strptime format, and the ptype label does
            # not name one: "01-01-2020" and "01/02/2020" both come back as
            # "date-eu". Read the layout off the values, and stay Text when
            # nothing fits, which is what happened for every date before this.
            elif dashai_info["type"] == "Date":
                detected = detect_date_format(data[col_name].dropna(), hint=ptype_type)
                if detected is None:
                    dashai_info = {
                        "type": "Text",
                        "dtype": "string",
                        "encoding": "utf-8",
                    }
                else:
                    dashai_info["dtype"] = detected

            reason = getattr(col_object, "inference_reason", None)
            if reason is not None:
                reason = {**reason}
                reason["final_type"] = dashai_info.get("type")
                reason["ptype_final"] = ptype_type
                reason["is_categorical"] = ptype_type == "categorical"
                non_null = data[col_name].dropna()
                reason["sample_values"] = (
                    non_null.drop_duplicates().head(5).astype(str).tolist()
                    if len(non_null)
                    else []
                )
                if (
                    reason.get("rule") == "date_type_excluded"
                    and dashai_info.get("type") == "Text"
                ):
                    reason["rule"] = "date_detected_mapped_to_text"
            dashai_info["inference_reason"] = reason

            inferred_types[col_name] = dashai_info

        return inferred_types


# Dummy inference method to avoid letting DashAIPtype alone :)
class DummyCategoricalInference(InferenceMethod):
    """
    A dummy inference method that does nothing.
    This is used to ensure that DashAIPtype is not the only inference method.
    """

    def infer_types(self, data):
        """
        Dummy Inference method that returns a dummy predicted schema.

        Parameters
        ----------
        data : Any
            The input data for type inference.

        Returns
        -------
        dict
            A dummy predicted types schema.
        """
        inferred_types = {}

        for col in data.columns:
            series = data[col]
            dtype = series.dtype

            if dtype == "object" or isinstance(series.dropna().iloc[0], str):
                n_unique = series.nunique(dropna=True)
                if n_unique < 10:
                    result = PTYPE_TO_DASHAI["categorical"].copy()
                    result["dtype"] = "string"
                    result["encoder"] = "one_hot"
                    inferred_types[col] = result
                else:
                    inferred_types[col] = PTYPE_TO_DASHAI["string"]

            elif pd.api.types.is_integer_dtype(dtype):
                n_unique = series.nunique(dropna=True)
                if n_unique < 10:
                    result = PTYPE_TO_DASHAI["categorical"].copy()
                    result["dtype"] = "int64"
                    result["encoder"] = "label"
                    inferred_types[col] = result
                else:
                    inferred_types[col] = PTYPE_TO_DASHAI["integer"]
            elif pd.api.types.is_float_dtype(dtype):
                inferred_types[col] = PTYPE_TO_DASHAI["float"]
            elif pd.api.types.is_bool_dtype(dtype):
                inferred_types[col] = PTYPE_TO_DASHAI["boolean"]
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                # This method does no format detection, so it cannot produce a
                # usable Date. "string" is the same dict the date entry held
                # before Date was enabled, so behaviour here is unchanged.
                inferred_types[col] = PTYPE_TO_DASHAI["string"]
            else:
                inferred_types[col] = PTYPE_TO_DASHAI["string"]
        return inferred_types
