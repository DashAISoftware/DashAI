# flake8: noqa

import re
from pathlib import Path

import joblib
import numpy as np

from DashAI.back.types.inf.ptype.Machines import Machines
from DashAI.back.types.inf.ptype.Ptype import Ptype

CAT_TRAINED_TYPES = [
    "integer",
    "string",
    "float",
    "boolean",
    "date-iso-8601",
    "date-eu",
    "date-non-std-subtype",
    "date-non-std",
]

DATE_TYPES = [
    "date-iso-8601",
    "date-eu",
    "date-non-std-subtype",
    "date-non-std",
    "time",
]

DATE_PATTERNS = [
    # DD.MM.YYYY or DD.MM.YY
    r"^\d{1,2}\.\d{1,2}\.\d{2,4}$",
    # YYYY.MM.DD
    r"^\d{4}\.\d{1,2}\.\d{1,2}$",
    # DD/MM/YYYY, MM/DD/YYYY, YYYY/MM/DD
    r"^\d{1,4}[/\-\.]\d{1,2}[/\-\.]\d{1,4}$",
    # DD-MM-YYYY or similar
    r"^\d{1,2}-\d{1,2}-\d{2,4}$",
    # Time patterns HH:MM:SS or HH:MM
    r"^\d{1,2}:\d{2}(:\d{2})?$",
    # Datetime: YYYY-MM-DD HH:MM:SS
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?$",
]


def _looks_like_date(series) -> bool:
    """Check if most values in series look like dates/times."""
    sample = series.dropna().astype(str).head(100)
    if len(sample) == 0:
        return False

    match_count = 0
    for val in sample:
        val = val.strip()
        for pattern in DATE_PATTERNS:
            if re.match(pattern, val):
                match_count += 1
                break
    return (match_count / len(sample)) > 0.8


class PtypeCat(Ptype):
    """Ptype with categorical detection."""

    def __init__(self, cat_threshold=0.7, max_unique_ratio=0.05, max_unique_count=50):
        super().__init__()
        self.types = [
            "integer",
            "string",
            "float",
            "boolean",
            "date-iso-8601",
            "date-eu",
            "date-non-std-subtype",
            "date-non-std",
        ]
        self.machines = Machines(self.types)
        self.verbose = False
        self.lr_clf = joblib.load(Path(__file__).parent.joinpath("LR.sav"))
        self.scaler = joblib.load(Path(__file__).parent.joinpath("scaler.pkl"))

        # Thresholds
        self.cat_threshold = cat_threshold
        self.max_unique_ratio = max_unique_ratio
        self.max_unique_count = max_unique_count

    def _is_categorical_candidate(self, series, inferred_type):
        """Check if column should be considered for categorical.

        Returns
        -------
        (is_candidate, reason)
            is_candidate : bool, whether the column is eligible for the
                categorical classifier.
            reason : dict, explanation payload with at minimum a `rule` key
                identifying the branch that drove the decision, plus the
                supporting statistics (`unique_count`, `unique_ratio`,
                `total_count`, `thresholds`, optional `string_length`).
        """
        total = int(len(series))
        non_null = series.dropna()
        unique_count = int(non_null.nunique()) if total else 0
        unique_ratio = (unique_count / total) if total else 0.0

        reason = {
            "rule": "unknown",
            "inferred_base_type": inferred_type,
            "unique_count": unique_count,
            "unique_ratio": round(unique_ratio, 4),
            "total_count": total,
            "thresholds": {
                "max_unique_count": self.max_unique_count,
                "max_unique_ratio": self.max_unique_ratio,
                "cat_threshold": self.cat_threshold,
            },
        }

        if inferred_type in DATE_TYPES:
            reason["rule"] = "date_type_excluded"
            return False, reason

        if inferred_type == "boolean":
            reason["rule"] = "boolean_always_categorical"
            return True, reason

        if inferred_type not in ["string", "integer", "float"]:
            reason["rule"] = "unsupported_base_type"
            return False, reason

        if total == 0:
            reason["rule"] = "empty_column"
            return False, reason

        if inferred_type == "string" and _looks_like_date(series):
            reason["rule"] = "string_looks_like_date"
            return False, reason

        if unique_count > self.max_unique_count:
            reason["rule"] = "too_many_unique_values"
            return False, reason

        if total >= 20 and unique_ratio > self.max_unique_ratio:
            reason["rule"] = "unique_ratio_above_threshold"
            return False, reason

        if inferred_type == "string":
            lengths = series.astype(str).str.len()
            mean_len = float(lengths.mean()) if len(lengths) else 0.0
            std_len = float(lengths.std()) if len(lengths) else 0.0
            reason["string_length"] = {
                "mean": round(mean_len, 2),
                "std": round(std_len, 2),
            }
            if mean_len > 50:
                reason["rule"] = "string_too_long"
                return False, reason
            if std_len > 20 and unique_ratio > 0.3:
                reason["rule"] = "string_high_length_variance"
                return False, reason

        if inferred_type == "integer":
            if unique_count == total:
                reason["rule"] = "integer_all_unique"
                return False, reason

            try:
                vals = non_null.astype(float).to_numpy()
                if len(vals) > 1:
                    sorted_vals = np.sort(vals)
                    diffs = np.diff(sorted_vals)

                    if np.all(diffs == 1):
                        reason["rule"] = "integer_sequential_range"
                        return False, reason

                    if np.median(diffs) <= 2 and np.max(diffs) < 5:
                        reason["rule"] = "integer_dense_small_range"
                        return False, reason

                    value_range = sorted_vals[-1] - sorted_vals[0]
                    if value_range > 100 and unique_count < 20:
                        reason["rule"] = "integer_wide_range_few_values"
                        return True, reason

            except (ValueError, TypeError):
                pass

        if inferred_type == "float":
            try:
                vals = non_null.astype(float)
                is_whole = np.allclose(vals, vals.astype(int))
                if not is_whole:
                    reason["rule"] = "float_has_decimals"
                    return False, reason
                reason["float_is_whole"] = True
            except (ValueError, TypeError):
                pass

        reason["rule"] = "passes_categorical_filters"
        return True, reason

    def _column(self, df, col_name, logP, counts):
        """Returns Column with categorical detection."""
        col = super()._column(df, col_name, logP, counts)
        t_hat = col.inferred_type()

        is_candidate, reason = self._is_categorical_candidate(df[col_name], t_hat)
        col.inference_reason = reason

        if not is_candidate:
            col.set_p_t_cat(t_hat, 0.0)
            return col

        if t_hat in ["integer", "string", "float", "boolean"]:
            try:
                feats = col._get_features(counts)
                feats = feats[: len(CAT_TRAINED_TYPES)]
                feats[-2:] = self.scaler.transform(feats[-2:].reshape(1, -1))
                ind = np.where(self.lr_clf.classes_ == "categorical")[0][0]
                p_cat = self.lr_clf.predict_proba(feats.reshape(1, -1))[0][ind]
            except Exception:
                p_cat = 0.0
        else:
            p_cat = 0.0

        reason["p_categorical"] = float(p_cat)

        if t_hat == "boolean":
            # Boolean shortcut: keep the "always categorical" rule, do not
            # let the ML classifier downgrade the explanation.
            col.p_t = {k: 0.0 for k in col.p_t}
            col.p_t["categorical"] = 1.0
            col.type = "categorical"
            return col

        if p_cat >= self.cat_threshold:
            col.p_t = {k: 0.0 for k in col.p_t}
            col.p_t["categorical"] = 1.0
            col.type = "categorical"
            # Only overwrite the rule when the ML classifier was the deciding
            # factor (i.e. the structural filters alone weren't conclusive).
            if reason["rule"] == "passes_categorical_filters":
                reason["rule"] = "ml_classifier_categorical"
        else:
            col.set_p_t_cat(t_hat, p_cat)
            if reason["rule"] == "passes_categorical_filters":
                reason["rule"] = "ml_classifier_not_categorical"

        return col
