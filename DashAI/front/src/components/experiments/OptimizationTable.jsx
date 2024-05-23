import React, { useEffect, useState }  from "react";
import PropTypes from "prop-types";
import { DataGrid } from "@mui/x-data-grid";
import { Grid, Paper, Typography, TextField, MenuItem} from "@mui/material";
import { getComponents as getComponentsRequest } from "../../api/component";
import EditOptimizerDialog from "./EditOptimizerDialog";
import { useSnackbar } from "notistack";

/**
 * This component renders a table to display the models that are currently in the experiment
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 */
function OptimizationTable({ newExp, setNewExp }) {
  const { enqueueSnackbar } = useSnackbar();
  const [selectedOptimizer, setSelectedOptimizer] = useState({});
  const [compatibleModels, setCompatibleOptimizers] = useState([]);


  console.log("newExp:")
  console.log(newExp)

  const getCompatibleOptimizers = async () => {
    try {
      const optimizers = await getComponentsRequest({
        selectTypes: ["Optimizer"],
        relatedComponent: newExp.task_name,
      });
      setCompatibleOptimizers(optimizers);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain compatible optimizers");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };



  const handleUpdateParameters = (id) => (newValues) => {
    setNewExp((prevExp) => {
      console.log("prevExp")
      console.log(prevExp)
      return {
        ...prevExp,
        runs: prevExp.runs.map((run) => {
          if (run.id === id) {
            console.log("Caso 1:")
            console.log({...run,optimizer_name: selectedOptimizer[id],optimizer_parameters: newValues} )
            return { ...run,optimizer_name: selectedOptimizer[id] ,optimizer_parameters: newValues };
          }
          console.log("Caso 2:")
          console.log(run)
          return run;
        }),
      };
    });
  };

  const handleSelectedOptimizer = (value, id) => {
    setSelectedOptimizer((prevSelectedOptimizer) => {
      return{
      ...prevSelectedOptimizer,
      [id]: value,
      };
    });

    handleAddOptimizer(id);
  };



  const handleAddOptimizer = async (id) => {
    // sets the default values of the newly added optimizer, making optional the parameter configuration

    if (!selectedOptimizer[id]){
      return ;
    }

    const optimizerRun= newExp.runs.map(run => {
      if (run.id === id) {
        return {
          ...run,
          optimizer_name: selectedOptimizer[id],
        };
      }
      return run;
    });

    setNewExp((prevNewExp) => {
      return {
      ...newExp,
      runs: optimizerRun,
      };
    });

  };

  // in mount, fetches the compatible models with the previously selected task
  useEffect(() => {
    getCompatibleOptimizers();
  }, []);

  const columns = React.useMemo(
    () => [
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
        headerName:"Select Optimizer",
        minWidth: 300,
        renderCell: (params) => ( 
          <>
            <TextField
            select
            label="Select an optimizer to add"
            value={selectedOptimizer[params.row.id] || ""}
            onChange={(e) => {
                handleSelectedOptimizer(e.target.value, params.row.id);
              
            }}
            fullWidth
          >
            {compatibleModels.map((optimizer) => (
              <MenuItem key={optimizer.name} value={optimizer.name}>
                {optimizer.name}
              </MenuItem>
            ))}
          </TextField>
        </>
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
        />
      ];
    },
    },
    ] );
  

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
