import React, { useState } from "react";
import PropTypes from "prop-types";

import {
  AddCircleOutline as AddIcon,
  Update as UpdateIcon,
} from "@mui/icons-material";
import { DataGrid, GridToolbar } from "@mui/x-data-grid";
import { Button, Grid, Paper, Typography } from "@mui/material";
import { useSnackbar } from "notistack";

import {
  getExperiments as getExperimentsRequest,
  deleteExperiment as deleteExperimentRequest,
} from "../../api/experiment";
import { formatDate } from "../../utils";
import RunnerDialog from "./RunnerDialog";
import Results from "../../pages/results/Results";

import DeleteItemModal from "../custom/DeleteItemModal";
import PipelinesModal from "./PipelinesModal";

function ExperimentsTable({
  handleOpenNewExperimentModal,
  updateTableFlag,
  setUpdateTableFlag,
}) {
  const [loading, setLoading] = useState(true);
  const [experiments, setExperiments] = useState([]);
  const { enqueueSnackbar } = useSnackbar();
  const [expRunning, setExpRunning] = useState({});

  const getExperiments = async () => {
    setLoading(true);
    try {
      const experiments = await getExperimentsRequest();
      setExperiments(experiments);
      console.log(experiments)
      // initially set all experiments running state to false
      const initialRunningState = experiments.reduce((accumulator, current) => {
        return { ...accumulator, [current.id]: false };
      }, {});
      setExpRunning(initialRunningState);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the experiment table.");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const deleteExperiment = async (id) => {
    try {
      await deleteExperimentRequest(id);

      enqueueSnackbar("Experiment successfully deleted.", {
        variant: "success",
      });
    } catch (error) {
      console.error(error);
      enqueueSnackbar("Error when trying to delete the experiment.");
    }
  };

  // Fetch experiments when the component is mounting
  React.useEffect(() => {
    getExperiments();
  }, []);

  // triggers an update of the table when updateTableFlag is set to true
  React.useEffect(() => {
    if (updateTableFlag) {
      setUpdateTableFlag(false);
      getExperiments();
    }
  }, [updateTableFlag]);

  const handleUpdateExperiments = () => {
    getExperiments();
  };

  const handleDeleteExperiment = (id) => {
    deleteExperiment(id);
    getExperiments();
  };

  const columns = React.useMemo(
    () => [
      {
        field: "id",
        headerName: "ID",
        minWidth: 30,
        editable: false,
      },
      {
        field: "name",
        headerName: "Name",
        minWidth: 250,
        editable: false,
      },
      {
        field: "task_name",
        headerName: "Task",
        minWidth: 200,
        editable: false,
      },
      {
        field: "dataset_id",
        headerName: "Dataset",
        minWidth: 200,
        editable: false,
      },
      {
        field: "created",
        headerName: "Created",
        minWidth: 140,
        editable: false,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "last_modified",
        headerName: "Edited",
        type: Date,
        minWidth: 140,
        editable: false,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 180,
        getActions: (params) => [
          <RunnerDialog
            key="runner-dialog"
            experiment={params.row}
            expRunning={expRunning}
            setExpRunning={setExpRunning}
          />,
          <Results key="runs-dialog" experiment={params.row} />,
          <DeleteItemModal
            key="delete-button"
            deleteFromTable={() => handleDeleteExperiment(params.id)}
          />,
          <PipelinesModal key="pipelines-modal" experiment={params.row} />,
        ],
      },
    ],
    [handleDeleteExperiment],
  );

  return (
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
                onClick={handleOpenNewExperimentModal}
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
        sortModel={[{ field: "id", sort: "desc" }]}
        columnVisibilityModel={{ id: false }}
        pageSizeOptions={[5, 10]}
        disableRowSelectionOnClick
        autoHeight
        loading={loading}
        slots={{
          toolbar: GridToolbar,
        }}
      />
    </Paper>
  );
}

ExperimentsTable.propTypes = {
  handleOpenNewExperimentModal: PropTypes.func,
  updateTableFlag: PropTypes.bool.isRequired,
  setUpdateTableFlag: PropTypes.func.isRequired,
};

export default ExperimentsTable;
