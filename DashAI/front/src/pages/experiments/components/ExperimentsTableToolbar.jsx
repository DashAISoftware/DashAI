import {
  AddCircleOutline as AddIcon,
  Update as UpdateIcon,
} from "@mui/icons-material";
import { Box, Button, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

function ExperimentsTableToolbar({
  handleOpenNewExperimentModal,
  handleUpdateExperiments,
}) {
  return (
    <Box display="flex" alignItems="center" gap={2}>
      <Box flex={1}>
        <Typography variant="h5" component="h2">
          Current experiments
        </Typography>
      </Box>
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
