import React from "react";
import PropTypes from "prop-types";

import { Tooltip } from "@mui/material";
import { GridActionsCellItem } from "@mui/x-data-grid";

function TooltipedCellItem({
  icon,
  tooltip,
  label,
  onClick = () => {},
  tooltipProps = {},
  ...props
}) {
  return (
    <Tooltip title={tooltip} onClick={onClick} {...tooltipProps}>
      {/* This span allows tooltip when the element is disabled */}
      <span>
        <GridActionsCellItem icon={icon} label={label} {...props} />
      </span>
    </Tooltip>
  );
}

TooltipedCellItem.propTypes = {
  icon: PropTypes.element.isRequired,
  tooltip: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  handleAction: PropTypes.func.isRequired,
  tooltipProps: PropTypes.object,
};

export default TooltipedCellItem;
