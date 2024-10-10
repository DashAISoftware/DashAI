import React, { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";

import { Box } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { useSnackbar } from "notistack";

import { formatDate } from "../../utils";
import DeleteItemModal from "../custom/DeleteItemModal";

import { useExplorationsContext } from "./context";
import {
  EditExplorationAction,
  RunExplorationAction,
  ViewExplorationResultsAction,
} from "./actions";

import {
  getExplorationsByDatasetId,
  deleteExploration,
} from "../../api/exploration";

function ExplorationsTable({
  updateTableFlag = false,
  setUpdateTableFlag = (value) => {},
  onExplorationSelect = (data) => {},
  onExplorationRun = (data) => {},
}) {
  const { explorationData } = useExplorationsContext();
  const { dataset_id: datasetId } = explorationData;
  const { enqueueSnackbar } = useSnackbar();

  const [loading, setLoading] = useState(false);
  const [explorations, setExplorations] = useState([]);

  const getExplorations = () => {
    setLoading(true);
    getExplorationsByDatasetId(datasetId)
      .then((response) => {
        setExplorations(response);
      })
      .catch((error) => {
        console.log(error);
        enqueueSnackbar("Error while trying to fetch explorations", {
          variant: "error",
        });
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleSelectExploration = (data) => {
    onExplorationSelect(data);
  };

  const handleRunExploration = (data) => {
    onExplorationRun(data);
  };

  const handleDeleteExploration = (id) => {
    setLoading(true);
    deleteExploration(id)
      .then(() => {
        getExplorations();
        enqueueSnackbar("Exploration deleted successfully", {
          variant: "success",
        });
      })
      .catch((error) => {
        console.log(error);
        enqueueSnackbar("Error while trying to delete the exploration", {
          variant: "error",
        });
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // Fetch explorations when the component is mounting
  useEffect(() => {
    getExplorations();
  }, []);

  // triggers an update of the table when updateFlag is set to true
  useEffect(() => {
    if (updateTableFlag) {
      setUpdateTableFlag(false);
      getExplorations();
    }
  }, [updateTableFlag]);

  // Columns definition
  const columns = useMemo(
    () => [
      {
        field: "id",
        headerName: "ID",
        minWidth: 30,
      },
      {
        field: "name",
        headerName: "Name",
        flex: 1,
        minwidth: 200,
      },
      {
        field: "created",
        headerName: "Created",
        width: 200,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "last_modified",
        headerName: "Edited",
        width: 200,
        valueFormatter: (params) => formatDate(params.value),
      },
      {
        field: "actions",
        headerName: "Actions",
        flex: 1,
        minWidth: 150,
        type: "actions",
        getActions: (params) => [
          <EditExplorationAction
            key="edit-button"
            onAction={() => handleSelectExploration(params.row)}
          />,
          <RunExplorationAction
            key="run-button"
            onAction={() => handleRunExploration(params.row)}
          />,
          <ViewExplorationResultsAction
            key="view-results-button"
            onAction={() => {}}
          />,
          <DeleteItemModal
            key="delete-button"
            deleteFromTable={() => handleDeleteExploration(params.row.id)}
          />,
        ],
      },
    ],
    [setUpdateTableFlag],
  );

  return (
    <Box sx={{ height: "100%", width: "100%" }}>
      <DataGrid
        loading={loading}
        autoHeight
        rows={explorations}
        columns={columns}
        disableRowSelectionOnClick
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
          sorting: {
            sortModel: [{ field: "updated", sort: "desc" }],
          },
        }}
        pageSizeOptions={[5, 10]}
      />
    </Box>
  );
}

ExplorationsTable.propTypes = {
  updateTableFlag: PropTypes.bool,
  setUpdateTableFlag: PropTypes.func,
  onExplorationSelect: PropTypes.func,
};

export default ExplorationsTable;
