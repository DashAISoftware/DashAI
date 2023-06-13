import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { PlayArrow as PlayArrowIcon } from "@mui/icons-material";
import { DataGrid, GridActionsCellItem } from "@mui/x-data-grid";
import {
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Typography,
} from "@mui/material";
import { getRuns as getRunsRequest } from "../../api/run";
import { executeRun as executeRunRequest } from "../../api/runner";
import { useSnackbar } from "notistack";

function RunnerDialog({ experiment }) {
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [rowSelectionModel, setRowSelectionModel] = useState([]);

  const getRuns = async () => {
    setLoading(true);
    try {
      const runs = await getRunsRequest(experiment.id.toString());
      setRows(runs);
      setRowSelectionModel(runs.map((run, idx) => run.id));
    } catch (error) {
      enqueueSnackbar(
        `Error while trying to obtain the runs associated to ${experiment.name}`,
        {
          variant: "error",
          anchorOrigin: {
            vertical: "top",
            horizontal: "right",
          },
        },
      );
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const executeRuns = async () => {
    for (const runId of rowSelectionModel) {
      try {
        await executeRunRequest(runId);
      } catch (error) {
        enqueueSnackbar(
          `Error while trying to execute the run ${
            rows.find((row) => row.id === runId).name
          }`,
          {
            variant: "error",
            anchorOrigin: {
              vertical: "top",
              horizontal: "right",
            },
          },
        );
        if (error.response) {
          console.error("Response error:", error.message);
        } else if (error.request) {
          console.error("Request error", error.request);
        } else {
          console.error("Unkown Error", error.message);
        }
      }
    }
  };

  const columns = [
    {
      field: "name",
      headerName: "Name",
      minWidth: 250,
      editable: false,
    },
    {
      field: "model_name",
      headerName: "Model Name",
      minWidth: 300,
      editable: false,
    },
    {
      field: "status",
      headerName: "Status",
      minWidth: 100,
      editable: false,
    },
  ];

  // on mount, fetches runs associated to the experiment.
  useEffect(() => {
    getRuns();
  }, []);
  return (
    <React.Fragment>
      <GridActionsCellItem
        key="runner-button"
        icon={<PlayArrowIcon />}
        label="Run"
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
          <Paper sx={{ px: 3, py: 2 }}>
            <Typography variant="subtitle1" component="h3" sx={{ pb: 1 }}>
              Select runs to execute
            </Typography>
            {!loading ? (
              <DataGrid
                rows={rows}
                columns={columns}
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
              />
            ) : (
              <CircularProgress color="inherit" />
            )}
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button
            variant="contained"
            endIcon={<PlayArrowIcon />}
            size="large"
            onClick={() => {
              setOpen(false);
              executeRuns();
            }}
          >
            Execute
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}

RunnerDialog.propTypes = {
  experiment: PropTypes.shape({
    name: PropTypes.string,
    id: PropTypes.number,
  }).isRequired,
};

export default RunnerDialog;
