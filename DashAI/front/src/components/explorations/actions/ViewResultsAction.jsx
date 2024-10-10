import React from "react";
import PropTypes from "prop-types";

import { Tooltip } from "@mui/material";
import { QueryStats as QueryStatsIcon } from "@mui/icons-material";
import { GridActionsCellItem } from "@mui/x-data-grid";

const tooltips = {
  enabled: "View Results",
  disabled: "disabled",
};

function ViewResultsAction({
  onAction = () => {},
  disabled = false,
  ...props
}) {
  const handleAction = () => {
    if (disabled) return;
    onAction();
  };

  const { color, tooltip } = (() => {
    switch (disabled) {
      case true:
        return { color: "", tooltip: tooltips.disabled };
      case false:
        return { color: "primary.main", tooltip: tooltips.enabled };
      default:
        return { color: "", tooltip: "" };
    }
  })();

  return (
    <React.Fragment>
      <Tooltip title={tooltip} onClick={() => handleAction()}>
        {/* This span allow tooltip when the element is disabled */}
        <span>
          <GridActionsCellItem
            icon={<QueryStatsIcon />}
            label="View Results"
            sx={{ color: color }}
            disabled={disabled}
            {...props}
          />
        </span>
      </Tooltip>
    </React.Fragment>
  );
}

ViewResultsAction.propTypes = {
  onSelect: PropTypes.func,
  disabled: PropTypes.bool,
};

export default ViewResultsAction;
