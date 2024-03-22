import { Paper, Typography } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { useSnackbar } from "notistack";
import PropTypes from "prop-types";
import React from "react";
import { runnersColumns } from "../constants/table";
import useExperimentsRuns from "../hooks/useExperimentsRuns";

function ExperimentsRunnerContentDialog({
  rowSelectionModel,
  setRowSelectionModel,
  experiment,
  expRunning,
  setExpRunning,
  finishedRunning,
  setFinishedRunning,
}) {
  const { enqueueSnackbar } = useSnackbar();

  const { runs: rows, loading } = useExperimentsRuns({
    experiment,
    expRunning,
    onSuccess: (runs) => {
      const firstRunInExecution = runs.find((run) => run.status === "Started"); // searches for a run with the status "running"
      if (firstRunInExecution !== undefined) {
        // modify state only if the value changes
        if (!expRunning[experiment.id]) {
          setExpRunning({ ...expRunning, [experiment.id]: true });
        }
      }

      if (rowSelectionModel.length === 0) {
        setRowSelectionModel(runs.map((run, idx) => run.id));
      }

      if (expRunning[experiment.id]) {
        const allRunsFinished = runs
          .filter((run) => rowSelectionModel.includes(run.id)) // get only the runs that have been selected to be sent to the runner
          .every((run) => {
            return ["Finished", "Error"].includes(run.status);
          }); // finished or error

        if (allRunsFinished) {
          setExpRunning({ ...expRunning, [experiment.id]: false });
          // only shows snackbar one time
          if (!finishedRunning) {
            enqueueSnackbar(`${experiment.name} has completed all its runs`, {
              variant: "success",
            });
            setFinishedRunning(true);
          }
        }
      }
    },
  });
  return (
    <Paper
      sx={{ px: 3, py: 2 }}
      // solves a mui problem related to putting datagrid inside another datagrid
      onClick={(event) => {
        event.target = document.body;
      }}
    >
      <Typography variant="subtitle1" component="h3" sx={{ pb: 1 }}>
        Select models to run
      </Typography>
      <DataGrid
        rows={rows}
        columns={runnersColumns}
        checkboxSelection
        onRowSelectionModelChange={(newRowSelectionModel) => {
          setRowSelectionModel(newRowSelectionModel);
        }}
        rowSelectionModel={rowSelectionModel}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
        }}
        pageSizeOptions={[5]}
        disableRowSelectionOnClick
        autoHeight
        loading={loading}
      />
    </Paper>
  );
}

ExperimentsRunnerContentDialog.propTypes = {
  rowSelectionModel: PropTypes.array.isRequired,
  setRowSelectionModel: PropTypes.func.isRequired,
  experiment: PropTypes.shape({
    name: PropTypes.string,
    id: PropTypes.number,
  }).isRequired,
  expRunning: PropTypes.objectOf(PropTypes.bool).isRequired,
  setExpRunning: PropTypes.func.isRequired,
  finishedRunning: PropTypes.bool.isRequired,
  setFinishedRunning: PropTypes.func.isRequired,
};

export default ExperimentsRunnerContentDialog;
