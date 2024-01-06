import { Box, Button, Typography } from "@mui/material";
import {
  AddCircleOutline as AddIcon,
  Update as UpdateIcon,
} from "@mui/icons-material";
import PropTypes from "prop-types";
import React from "react";

function ExperimentsTableToolbar({
  handleOpenNewExperimentModal,
  handleUpdateExperiments,
}) {
  return (
    <Box display="flex" alignItems="center">
      <Typography variant="h5" component="h2">
        Current experiments
      </Typography>

      <Button
        variant="contained"
        onClick={handleOpenNewExperimentModal}
        endIcon={<AddIcon />}
      >
        New Experiment
      </Button>

      <Button
        variant="contained"
        onClick={handleUpdateExperiments}
        endIcon={<UpdateIcon />}
      >
        Update
      </Button>
    </Box>
  );
}

ExperimentsTableToolbar.propTypes = {
  handleOpenNewExperimentModal: PropTypes.func,
  handleUpdateExperiments: PropTypes.func,
};

export default ExperimentsTableToolbar;
