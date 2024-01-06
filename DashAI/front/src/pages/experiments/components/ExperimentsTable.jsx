import PropTypes from "prop-types";
import React, { useState } from "react";

import { DataGrid } from "@mui/x-data-grid";
import { useSnackbar } from "notistack";

import {
  deleteExperiment as deleteExperimentRequest,
  getExperiments as getExperimentsRequest,
} from "../../api/experiment";
import { formatDate } from "../../utils";
import RunnerDialog from "./RunnerDialog";

import DeleteItemModal from "../custom/DeleteItemModal";
import ExperimentsTableLayout from "./ExperimentsTableLayout";
import ExperimentsTableToolbar from "./ExperimentsTableToolbar";

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
        minWidth: 80,
        getActions: (params) => [
          <RunnerDialog
            key="runner-dialog"
            experiment={params.row}
            expRunning={expRunning}
            setExpRunning={setExpRunning}
          />,
          <DeleteItemModal
            key="delete-button"
            deleteFromTable={() => handleDeleteExperiment(params.id)}
          />,
        ],
      },
    ],
    [handleDeleteExperiment],
  );

  return (
    <ExperimentsTableLayout
      toolbar={
        <ExperimentsTableToolbar
          handleOpenNewExperimentModal={handleOpenNewExperimentModal}
          handleUpdateExperiments={handleOpenNewExperimentModal}
        />
      }
    >
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
      />
    </ExperimentsTableLayout>
  );
}

ExperimentsTable.propTypes = {
  handleOpenNewExperimentModal: PropTypes.func,
  updateTableFlag: PropTypes.bool.isRequired,
  setUpdateTableFlag: PropTypes.func.isRequired,
};

export default ExperimentsTable;
