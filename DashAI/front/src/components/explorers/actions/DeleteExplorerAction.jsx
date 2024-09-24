import React from "react";
import PropTypes from "prop-types";

import { Tooltip } from "@mui/material";
import { DeleteForever as DeleteIcon } from "@mui/icons-material";
import { GridActionsCellItem } from "@mui/x-data-grid";
import { useSnackbar } from "notistack";

import { deleteExplorer } from "../../../api/explorer";

function DeleteExplorerAction({
  explorerId,
  setUpdateTableFlag = () => {},
  ...props
}) {
  const { enqueueSnackbar } = useSnackbar();

  const handleAction = async (explorerId) => {
    console.log("Delete exploration", explorerId);
    // TODO: Implement delete exploration confirmation modal

    setUpdateTableFlag(true);
    enqueueSnackbar(`[Fake] Exploration with ID: ${explorerId} deleted`, {
      variant: "success",
    });
  };

  return (
    <React.Fragment>
      <Tooltip
        title="Delete the exploration"
        onClick={() => handleAction(explorerId)}
      >
        {/* This span allow tooltip when the element is disabled */}
        <span>
          <GridActionsCellItem
            icon={<DeleteIcon />}
            label="Delete"
            sx={{ color: "error.main" }}
            {...props}
          />
        </span>
      </Tooltip>
    </React.Fragment>
  );
}

DeleteExplorerAction.propTypes = {
  explorerId: PropTypes.number.isRequired,
  setUpdateTableFlag: PropTypes.func,
};

export default DeleteExplorerAction;
