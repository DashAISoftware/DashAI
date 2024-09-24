import React from "react";
import PropTypes from "prop-types";

import { Tooltip } from "@mui/material";
import {
  PushPin as PinIcon,
  BookmarkAdded as PinnedIcon,
} from "@mui/icons-material";
import { GridActionsCellItem } from "@mui/x-data-grid";

import { useSnackbar } from "notistack";

const tooltips = {
  enabled: "Pin the exploration, so it won't be deleted",
  disabled: "This exploration is already pinned",
};
const icons = {
  enabled: <PinIcon />,
  disabled: <PinnedIcon />,
};

function PinExplorerAction({
  explorerId,
  setUpdateTableFlag = () => {},
  disabled = false,
  ...props
}) {
  const { enqueueSnackbar } = useSnackbar();
  const handleAction = async (explorerId) => {
    if (disabled) return;
    // TODO: Implement the pin action

    setUpdateTableFlag(true);
    enqueueSnackbar(`[Fake] Exploration with ID: ${explorerId} pinned`, {
      variant: "success",
    });
  };
  const color = disabled ? "primary.main" : "";
  const icon = disabled ? icons.disabled : icons.enabled;

  return (
    <React.Fragment>
      <Tooltip
        title={disabled ? tooltips.disabled : tooltips.enabled}
        onClick={() => handleAction(explorerId)}
      >
        {/* This span allow tooltip when the element is disabled */}
        <span>
          <GridActionsCellItem
            icon={icon}
            label="Pin"
            sx={{ color: color }}
            disabled={disabled}
            {...props}
          />
        </span>
      </Tooltip>
    </React.Fragment>
  );
}

PinExplorerAction.propTypes = {
  explorerId: PropTypes.number.isRequired,
  setUpdateTableFlag: PropTypes.func,
  disabled: PropTypes.bool,
};

export default PinExplorerAction;
