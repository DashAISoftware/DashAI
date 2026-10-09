import React from "react";
import PropTypes from "prop-types";
import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import StorageIcon from "@mui/icons-material/Storage";
import CreateIcon from "@mui/icons-material/Create";
import { useTranslation } from "react-i18next";

/**
 * Chooses where the instances to explain come from: an existing dataset or
 * values typed in by hand.
 */
export default function ExplainerSourceToggle({ source, onChange }) {
  const { t } = useTranslation(["explainers"]);

  return (
    <ToggleButtonGroup
      value={source}
      exclusive
      onChange={(_e, value) => {
        if (value) onChange(value);
      }}
      size="small"
      fullWidth
      sx={{ mb: 4 }}
    >
      <ToggleButton value="dataset">
        <StorageIcon fontSize="small" sx={{ mr: 2 }} />
        {t("explainers:label.sourceFromDataset")}
      </ToggleButton>
      <ToggleButton value="manual">
        <CreateIcon fontSize="small" sx={{ mr: 2 }} />
        {t("explainers:label.sourceManualInput")}
      </ToggleButton>
    </ToggleButtonGroup>
  );
}

ExplainerSourceToggle.propTypes = {
  source: PropTypes.oneOf(["dataset", "manual"]).isRequired,
  onChange: PropTypes.func.isRequired,
};
