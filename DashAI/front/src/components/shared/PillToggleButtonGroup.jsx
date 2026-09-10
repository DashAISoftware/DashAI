import React from "react";
import PropTypes from "prop-types";
import { ToggleButtonGroup } from "@mui/material";
import { useTheme } from "@mui/material/styles";

/**
 * Segmented pill selector matching the app's tab styling (the
 * Results/Predictions tabs, DatasetVisualization's tabs) — use this instead
 * of a bare MUI ToggleButtonGroup for any in-page filter/split control that
 * should look the same everywhere (e.g. Dataset/Manual, Train/Validation/Test).
 */
function PillToggleButtonGroup({ sx, ...props }) {
  const theme = useTheme();

  return (
    <ToggleButtonGroup
      exclusive
      {...props}
      sx={{
        minHeight: 40,
        bgcolor: theme.palette.ui.box,
        borderRadius: 1,
        "& .MuiToggleButtonGroup-grouped": {
          minHeight: 40,
          fontSize: "0.85rem",
          fontWeight: 400,
          textTransform: "none",
          border: "1px solid transparent",
          borderRadius: "4px !important",
          color: "text.secondary",
          "&:hover": { bgcolor: theme.palette.action.hover },
          "&.Mui-selected": {
            bgcolor: "background.paper",
            color: "primary.main",
            fontWeight: 600,
            borderBottom: `2px solid ${theme.palette.primary.main}`,
            "&:hover": { bgcolor: "background.paper" },
          },
        },
        ...sx,
      }}
    />
  );
}

PillToggleButtonGroup.propTypes = {
  sx: PropTypes.object,
};

PillToggleButtonGroup.defaultProps = {
  sx: {},
};

export default PillToggleButtonGroup;
