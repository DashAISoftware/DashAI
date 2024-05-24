import { Grid, Paper, Typography } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import PropTypes from "prop-types";
import React, { useState } from "react";

import EditOptimizerDialog from "./EditOptimizerDialog";
import OptimizationTableSelectOptimizer from "./OptimizationTableSelectOptimizer";

/**
 * This component renders a table to display the models that are currently in the experiment
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 */
function OptimizationTable({ newExp, setNewExp }) {
  const [selectedOptimizer, setSelectedOptimizer] = useState({});

  const handleUpdateParameters = (id) => (newValues) => {
    setNewExp((prevExp) => {
      return {
        ...prevExp,
        runs: prevExp.runs.map((run) => {
          if (run.id === id) {
            return {
              ...run,
              optimizer_name: selectedOptimizer[id],
              optimizer_parameters: newValues,
            };
          }
          return run;
        }),
      };
    });
  };

  const handleAddOptimizer = async (name, defaultValues, id) => {
    // sets the default values of the newly added optimizer, making optional the parameter configuration

    const optimizerRun = newExp.runs.map((run) => {
      if (run.id === id) {
        return {
          ...run,
          optimizer_name: name,
          optimizer_parameters: defaultValues,
        };
      }
      return run;
    });

    setNewExp((prevExp) => {
      return {
        ...prevExp,
        runs: optimizerRun,
      };
    });
  };

  const handleSelectedOptimizer = async (name, defaultValues, id) => {
    setSelectedOptimizer((prevSelectedOptimizer) => {
      return {
        ...prevSelectedOptimizer,
        [id]: name,
      };
    });

    handleAddOptimizer(name, defaultValues, id);
  };

  const columns = React.useMemo(() => [
    {
      field: "name",
      headerName: "Name",
      minWidth: 300,
      editable: false,
    },
    {
      field: "model",
      headerName: "Model",
      minWidth: 300,
      editable: false,
    },
    {
      field: "optimizer",
      headerName: "Select Optimizer",
      minWidth: 300,
      renderCell: (params) => (
        <OptimizationTableSelectOptimizer
          taskName={newExp.task_name}
          optimizerName={selectedOptimizer[params.row.id]}
          handleSelectedOptimizer={(optimizerName, defaultValues) =>
            handleSelectedOptimizer(optimizerName, defaultValues, params.row.id)
          }
        />
      ),
    },
    {
      field: "actions",
      type: "actions",
      minWidth: 100,
      getActions: (params) => {
        if (!selectedOptimizer[params.row.id]) {
          return [];
        }

        return [
          <EditOptimizerDialog
            key="edit-component"
            optimizerToConfigure={selectedOptimizer[params.row.id]}
            updateParameters={handleUpdateParameters(params.row.id)}
            paramsInitialValues={params.row.optimizer_parameters}
          />,
        ];
      },
    },
  ]);

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

OptimizationTable.propTypes = {
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

export default OptimizationTable;
