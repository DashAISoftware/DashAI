import React from "react";
import PropTypes from "prop-types";

import {
  AddCircleOutline as AddIcon,
  Delete as DeleteIcon,
  Update as UpdateIcon,
} from "@mui/icons-material";
import { DataGrid, GridActionsCellItem } from "@mui/x-data-grid";
import { Button, Grid, Paper, Typography } from "@mui/material";
import { useSnackbar } from "notistack";

import {
  getExperiments as getExperimentsRequest,
  deleteExperiment as deleteExperimentRequest,
} from "../api/experiment.ts";
import { formatDate } from "../utils";

function ExperimentsTable({ handleNewExperiment }) {
  const [loading, setLoading] = React.useState(true);
  const [experiments, setExperiments] = React.useState([]);
  const { enqueueSnackbar } = useSnackbar();

  const getExperiments = async () => {
    setLoading(true);
    try {
      const experiments = await getExperimentsRequest();
      setExperiments(experiments);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the experiment table.", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
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

  const deleteExperiment = async (id) => {
    try {
      deleteExperimentRequest(id);
      setExperiments(getExperiments);

      enqueueSnackbar("Experiment successfully deleted.", {
        variant: "success",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
    } catch (error) {
      console.error(error);
      enqueueSnackbar("Error when trying to delete the experiment.", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
    }
  };

  // Fetch experiments when the component is mounting
  React.useEffect(() => {
    getExperiments();
  }, []);

  const handleUpdateExperiments = () => {
    getExperiments();
  };

  const handleDeleteExperiment = (id) => {
    deleteExperiment(id);
  };

  const columns = React.useMemo(
    () => [
      {
        field: "name",
        headerName: "Name",
        minWidth: 250,
        editable: false,
      },
      {
        field: "taskName",
        headerName: "Task",
        minWidth: 200,
        editable: false,
      },
      {
        field: "dataset",
        headerName: "Dataset",
        minWidth: 200,
        editable: false,
      },
      {
        field: "created",
        headerName: "Created",
        minWidth: 120,
        editable: false,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "edited",
        headerName: "Edited",
        type: Date,
        minWidth: 120,
        editable: false,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 80,
        getActions: (params) => [
          <GridActionsCellItem
            key="delete-button"
            icon={<DeleteIcon />}
            label="Delete"
            onClick={handleDeleteExperiment(params.id)}
          />,
        ],
      },
    ],
    [handleDeleteExperiment]
  );

  return (
    <React.Fragment>
      <Paper sx={{ py: 4, px: 6 }}>
        {/* Title and new experiment button */}
        <Grid
          container
          direction="row"
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 4 }}
        >
          <Typography variant="h5" component="h2">
            Current experiments
          </Typography>
          <Grid item>
            <Grid container spacing={2}>
              <Grid item>
                <Button
                  variant="contained"
                  onClick={handleNewExperiment}
                  endIcon={<AddIcon />}
                >
                  New Experiment
                </Button>
              </Grid>
              <Grid item>
                <Button
                  variant="contained"
                  onClick={handleUpdateExperiments}
                  endIcon={<UpdateIcon />}
                >
                  Update
                </Button>
              </Grid>
            </Grid>
          </Grid>
        </Grid>

        {/* Experiments Table */}
        <DataGrid
          rows={experiments}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: 5,
              },
            },
          }}
          pageSizeOptions={[10]}
          disableRowSelectionOnClick
          autoHeight
          loading={loading}
        />
      </Paper>
    </React.Fragment>
  );
}

ExperimentsTable.propTypes = {
  handleNewExperiment: PropTypes.func,
};

export default ExperimentsTable;
