import React from "react";
import PropTypes from "prop-types";

import { Tooltip } from "@mui/material";
import { QueryStats as QueryStatsIcon } from "@mui/icons-material";
import { GridActionsCellItem } from "@mui/x-data-grid";

import { ExplorerStatus } from "../../../types/explorer";
import { useExplorerContext } from "../context/ExplorerContext";

const tooltips = {
  NOT_STARTED: "Go Launch the exploration",
  DELIVERED: "Wait for the results",
  STARTED: "Wait for the results",
  FINISHED: "Go see the results",
  ERROR: "Go to relaunch the exploration",
  disabled: "You already selected this exploration",
};

function ViewResultAction({ explorerId, disabled = false, status, ...props }) {
  const { setExplorerId } = useExplorerContext();
  const handleAction = async (explorerId) => {
    if (disabled) return;
    setExplorerId(explorerId);
  };

  const { color, tooltip } = (() => {
    switch (status) {
      case ExplorerStatus.NOT_STARTED:
        return { color: "primary.secondary", tooltip: tooltips.NOT_STARTED };
      case ExplorerStatus.DELIVERED:
        return { color: "warning.main", tooltip: tooltips.DELIVERED };
      case ExplorerStatus.STARTED:
        return { color: "info.main", tooltip: tooltips.STARTED };
      case ExplorerStatus.FINISHED:
        return { color: "primary.main", tooltip: tooltips.FINISHED };
      case ExplorerStatus.ERROR:
        return { color: "error.main", tooltip: tooltips.ERROR };
      default:
        return { color: "", tooltip: null };
    }
  })();

  return (
    <React.Fragment>
      <Tooltip
        title={disabled ? tooltips.disabled : tooltip}
        onClick={() => handleAction(explorerId)}
      >
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

ViewResultAction.propTypes = {
  explorerId: PropTypes.number.isRequired,
  disabled: PropTypes.bool,
  status: PropTypes.number,
};

export default ViewResultAction;
