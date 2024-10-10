import React from "react";
import PropTypes from "prop-types";

import { Tooltip } from "@mui/material";
import { Edit as EditIcon } from "@mui/icons-material";
import { GridActionsCellItem } from "@mui/x-data-grid";

const tooltips = {
  enabled: "Edit Exploration",
  disabled: "disabled",
};

function EditAction({ onAction = () => {}, disabled = false, ...props }) {
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
            icon={<EditIcon />}
            label="Edit Exploration"
            sx={{ color: color }}
            disabled={disabled}
            {...props}
          />
        </span>
      </Tooltip>
    </React.Fragment>
  );
}

EditAction.propTypes = {
  onAction: PropTypes.func,
  disabled: PropTypes.bool,
};

export default EditAction;
