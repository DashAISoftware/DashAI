import React from "react";
import PropTypes from "prop-types";
import { DataGrid } from "@mui/x-data-grid";
import { Grid, Paper, Typography } from "@mui/material";
import DeleteModelDialog from "./DeleteModelDialog";
import EditModelDialog from "./EditModelDialog";

/**
 * This component renders a table to display the models that are currently in the experiment
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 */
function ModelsTable({ newExp, setNewExp }) {
  const handleDeleteModel = (id) => {
    setNewExp({
      ...newExp,
      runs: newExp.runs.filter((model) => model.id !== id),
    });
  };

  const handleUpdateParameters = (id) => (newValues) => {
    setNewExp((prevExp) => {
      return {
        ...prevExp,
        runs: prevExp.runs.map((model) => {
          if (model.id === id) {
            return { ...model, params: newValues };
          }
          return model;
        }),
      };
    });
  };

  const columns = React.useMemo(
    () => [
      {
        field: "name",
        headerName: "Name",
        minWidth: 450,
        editable: false,
      },
      {
        field: "model",
        headerName: "Model",
        minWidth: 450,
        editable: false,
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 100,
        getActions: (params) => [
          <EditModelDialog
            key="edit-component"
            modelToConfigure={params.row.model}
            updateParameters={handleUpdateParameters(params.id)}
            paramsInitialValues={params.row.params}
          />,
          <DeleteModelDialog
            key="delete-component"
            deleteFromTable={() => handleDeleteModel(params.id)}
          />,
        ],
      },
    ],
    [handleDeleteModel],
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
          Current models in the experiment
        </Typography>
      </Grid>

      {/* Models Table */}
      <DataGrid
        rows={newExp.runs}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
        }}
        pageSizeOptions={[5]}
        disableRowSelectionOnClick
        density="compact"
        autoHeight
        hideFooterSelectedRowCount
      />
    </Paper>
  );
}

ModelsTable.propTypes = {
  newExp: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    dataset: PropTypes.object,
    task_name: PropTypes.string,
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
};

export default ModelsTable;
