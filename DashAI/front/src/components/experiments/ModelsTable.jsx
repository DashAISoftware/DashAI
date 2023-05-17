import React from "react";
import PropTypes from "prop-types";
import { DataGrid } from "@mui/x-data-grid";
import { Grid, Paper, Typography } from "@mui/material";
import DeleteModelDialog from "./DeleteModelDialog";
import EditModelDialog from "./EditModelDialog";
// import { useSnackbar } from "notistack";

// import {
//   getExperiments as getExperimentsRequest,
//   deleteExperiment as deleteExperimentRequest,
// } from "../../api/experiment";
// import { formatDate } from "../../utils";

/**
 * This component renders a table to display the models that are currently in the experiment
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 */
function ModelsTable({ newExp, setNewExp }) {
  // const [loading, setLoading] = useState(true);
  // const [experiments, setExperiments] = useState([]);
  // const { enqueueSnackbar } = useSnackbar();

  // const getExperiments = async () => {
  //   setLoading(true);
  //   try {
  //     const experiments = await getExperimentsRequest();
  //     setExperiments(experiments);
  //   } catch (error) {
  //     enqueueSnackbar("Error while trying to obtain the experiment table.", {
  //       variant: "error",
  //       anchorOrigin: {
  //         vertical: "top",
  //         horizontal: "right",
  //       },
  //     });
  //     if (error.response) {
  //       console.error("Response error:", error.message);
  //     } else if (error.request) {
  //       console.error("Request error", error.request);
  //     } else {
  //       console.error("Unkown Error", error.message);
  //     }
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  // const deleteExperiment = async (id) => {
  //   try {
  //     deleteExperimentRequest(id);
  //     setExperiments(getExperiments);

  //     enqueueSnackbar("Experiment successfully deleted.", {
  //       variant: "success",
  //       anchorOrigin: {
  //         vertical: "top",
  //         horizontal: "right",
  //       },
  //     });
  //   } catch (error) {
  //     console.error(error);
  //     enqueueSnackbar("Error when trying to delete the experiment.", {
  //       variant: "error",
  //       anchorOrigin: {
  //         vertical: "top",
  //         horizontal: "right",
  //       },
  //     });
  //   }
  // };

  const handleDeleteModel = (id) => {
    setNewExp({
      ...newExp,
      runs: newExp.runs.filter((model) => model.id !== id),
    });
    // setModels(models.filter((model) => model.id !== id));
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
    // setModels((prevModels) => {
    //   return prevModels.map((model) => {
    //     if (model.id === id) {
    //       return { ...model, params: newValues };
    //     }
    //     return model;
    //   });
    // });
  };

  const columns = React.useMemo(
    () => [
      {
        field: "nickname",
        headerName: "Nickname",
        minWidth: 450,
        editable: false,
      },
      {
        field: "type",
        headerName: "Type",
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
            modelToConfigure={params.row.type}
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
