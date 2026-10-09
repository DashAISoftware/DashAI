import React from "react";
import PropTypes from "prop-types";
import { Tabs } from "@mui/material";
import { useTheme } from "@mui/material/styles";

/**
 * Segmented pill-bar tabs (Results/Predictions groups in the run detail
 * view, DatasetVisualization's tabs) — use this instead of a bare MUI Tabs
 * for any tab group that should look the same everywhere, including the
 * diagonal-stripe treatment for disabled tabs.
 */
function PillTabs({ sx, minHeight, ...props }) {
  const theme = useTheme();

  return (
    <Tabs
      {...props}
      sx={{
        minHeight,
        bgcolor: theme.palette.ui.box,
        borderRadius: 1,
        "& .MuiTabs-indicator": { height: "2px" },
        "& .MuiTab-root": {
          minHeight,
          fontSize: "0.85rem",
          borderRadius: "4px",
          transition: "all 0.2s",
          border: "1px solid transparent",
          textTransform: "none",
          "&:hover": { bgcolor: theme.palette.action.hover },
          "&.Mui-disabled": {
            color: theme.palette.text.disabled,
            bgcolor: theme.palette.ui.disabled,
            borderColor: theme.palette.ui.border,
            opacity: 0.6,
            cursor: "not-allowed",
            filter: "grayscale(0.6)",
            position: "relative",
            "&::after": {
              content: '""',
              position: "absolute",
              inset: 0,
              borderRadius: "4px",
              pointerEvents: "none",
              background:
                "repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0,0,0,0.1) 10px, rgba(0,0,0,0.1) 20px)",
            },
          },
        },
        ...sx,
      }}
    />
  );
}

PillTabs.propTypes = {
  sx: PropTypes.object,
  minHeight: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
};

PillTabs.defaultProps = {
  sx: {},
  minHeight: 40,
};

export default PillTabs;
