import React from "react";
import PropTypes from "prop-types";
import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import TuneIcon from "@mui/icons-material/Tune";
import ChecklistIcon from "@mui/icons-material/Checklist";
import { useTranslation } from "react-i18next";

/**
 * Chooses how rows are picked from the selected dataset: a percentage of the
 * chosen split, or rows marked by hand in the table.
 */
export default function RowSelectionModeToggle({ mode, onChange }) {
  const { t } = useTranslation(["explainers"]);

  return (
    <ToggleButtonGroup
      value={mode}
      exclusive
      onChange={(_e, value) => {
        if (value) onChange(value);
      }}
      size="small"
      fullWidth
    >
      <ToggleButton value="percentage">
        <TuneIcon fontSize="small" sx={{ mr: 2 }} />
        {t("explainers:label.rowModePercentage")}
      </ToggleButton>
      <ToggleButton value="manual">
        <ChecklistIcon fontSize="small" sx={{ mr: 2 }} />
        {t("explainers:label.rowModeManual")}
      </ToggleButton>
    </ToggleButtonGroup>
  );
}

RowSelectionModeToggle.propTypes = {
  mode: PropTypes.oneOf(["percentage", "manual"]).isRequired,
  onChange: PropTypes.func.isRequired,
};
