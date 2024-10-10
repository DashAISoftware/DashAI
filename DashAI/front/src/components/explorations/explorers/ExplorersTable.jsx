import React from "react";
import PropTypes from "prop-types";

import { DataGrid } from "@mui/x-data-grid";
import { Grid, Paper, Typography } from "@mui/material";

import DeleteItemModal from "../../custom/DeleteItemModal";
import { EditParametersDialog, EditColumnsDialog } from "..";
import { useExplorationsContext } from "../context";

function ExplorersTable({ explorerTypes = [] }) {
  const { explorationData, setExplorationData, datasetColumns } =
    useExplorationsContext();
  const { explorers } = explorationData;

  const handleDeleteExplorer = (id) => {
    setExplorationData((prev) => ({
      ...prev,
      explorers: prev.explorers.filter((explorer) => explorer.id !== id),
      deleted_explorers: [...prev.deleted_explorers, id],
    }));
  };

  const handleUpdateColumns = (id) => (newValues) => {
    let modifiedExplorer = explorers.find((explorer) => explorer.id === id);
    modifiedExplorer.columns = newValues;
    setExplorationData((prev) => ({
      ...prev,
      explorers: prev.explorers.map((explorer) =>
        explorer.id === id ? modifiedExplorer : explorer,
      ),
    }));
  };

  const handleUpdateParameters = (id) => (newValues) => {
    let modifiedExplorer = explorers.find((explorer) => explorer.id === id);
    modifiedExplorer.parameters = newValues;
    setExplorationData((prev) => ({
      ...prev,
      explorers: prev.explorers.map((explorer) =>
        explorer.id === id ? modifiedExplorer : explorer,
      ),
    }));
  };

  const columns = React.useMemo(
    () => [
      {
        field: "name",
        headerName: "Name",
        minWidth: 200,
        flex: 1,
      },
      {
        field: "exploration_type",
        headerName: "explorer Type",
        minWidth: 200,
        flex: 1,
      },
      {
        field: "actions",
        headerName: "Actions",
        type: "actions",
        minWidth: 100,
        flex: 0.5,
        getActions: (params) => [
          <EditColumnsDialog
            key="edit-columns"
            datasetColumns={datasetColumns}
            updateValue={handleUpdateColumns(params.id)}
            initialValues={params.row.columns}
            explorerType={explorerTypes.find(
              (explorer) => explorer.label === params.row.exploration_type,
            )}
          />,

          <EditParametersDialog
            key="edit-component"
            modelToConfigure={params.row.exploration_type}
            updateParameters={handleUpdateParameters(params.id)}
            paramsInitialValues={params.row.parameters}
          />,
          <DeleteItemModal
            key="delete-component"
            deleteFromTable={() => handleDeleteExplorer(params.id)}
          />,
        ],
      },
    ],
    [handleDeleteExplorer, explorerTypes, datasetColumns],
  );

  return (
    <Paper sx={{ py: 1, px: 2 }}>
      {/* Title */}
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 2 }}
      >
        <Typography variant="subtitle1" component="h3">
          Current explorers in the exploration
        </Typography>
      </Grid>

      {/* Models Table */}
      <DataGrid
        rows={explorers}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
        }}
        pageSizeOptions={[5]}
        density="compact"
        autoHeight
        hideFooterSelectedRowCount
        disableRowSelectionOnClick
      />
    </Paper>
  );
}

ExplorersTable.propTypes = {};

export default ExplorersTable;
