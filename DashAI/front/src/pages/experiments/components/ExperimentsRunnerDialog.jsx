import {
  Check as CheckIcon,
  PlayArrow as PlayArrowIcon,
} from "@mui/icons-material";
import { LoadingButton } from "@mui/lab";
import {
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import { GridActionsCellItem } from "@mui/x-data-grid";
import PropTypes from "prop-types";
import React, { useState } from "react";
import useExperimentsRunsPlay from "../hooks/useExperimentsRunsPlay";
import ExperimentsRunnerContentDialog from "./ExperimentsRunnerContentDialog";

/**
 * Modal for selecting the runs to be sent to execute in an experiment
 * @param {object} experiment contains the information of an experiment as received from the backend (IExperiment)
 */
function ExperimentsRunnerDialog({ experiment, expRunning, setExpRunning }) {
  const [open, setOpen] = useState(false);
  const [rowSelectionModel, setRowSelectionModel] = useState([]);
  const [finishedRunning, setFinishedRunning] = useState(false);

  const { handleExecuteRuns } = useExperimentsRunsPlay({
    expRunning,
    setExpRunning,
    experiment,
    rowSelectionModel,
  });
  return (
    <React.Fragment>
      <GridActionsCellItem
        key="runner-button"
        icon={
          expRunning[experiment.id] ? (
            <CircularProgress size={18} />
          ) : (
            <PlayArrowIcon />
          )
        }
        label="Run"
        disabled={
          !expRunning[experiment.id] &&
          Object.values(expRunning).some((value) => value === true)
        }
        onClick={() => setOpen(true)}
      />
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth={"md"}
      >
        <DialogTitle>{`Runs in ${experiment.name}`}</DialogTitle>
        <DialogContent>
          <ExperimentsRunnerContentDialog
            rowSelectionModel={rowSelectionModel}
            setRowSelectionModel={setRowSelectionModel}
            experiment={experiment}
            expRunning={expRunning}
            setExpRunning={setExpRunning}
            finishedRunning={finishedRunning}
            setFinishedRunning={setFinishedRunning}
          />
        </DialogContent>
        <DialogActions>
          <LoadingButton
            variant="contained"
            loading={expRunning[experiment.id]}
            endIcon={finishedRunning ? <CheckIcon /> : <PlayArrowIcon />}
            size="large"
            onClick={handleExecuteRuns}
          >
            {finishedRunning ? "Finished" : "Start"}
          </LoadingButton>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}

ExperimentsRunnerDialog.propTypes = {
  experiment: PropTypes.shape({
    name: PropTypes.string,
    id: PropTypes.number,
  }).isRequired,
  expRunning: PropTypes.objectOf(PropTypes.bool).isRequired,
  setExpRunning: PropTypes.func.isRequired,
};

export default ExperimentsRunnerDialog;
