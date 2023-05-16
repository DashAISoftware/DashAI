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

function ModelsTable({ models, setModels }) {
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
    setModels(models.filter((model) => model.id !== id));
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
    <Paper sx={{ py: 4, px: 6 }}>
      {/* Title */}
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 4 }}
      >
        <Typography variant="h5" component="h2">
          Current models in the experiment
        </Typography>
      </Grid>

      {/* Models Table */}
      <DataGrid
        rows={models}
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
        loading={false}
      />
    </Paper>
  );
}

ModelsTable.propTypes = {
  models: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number,
      nickname: PropTypes.string,
      type: PropTypes.string,
    }),
  ).isRequired,
  setModels: PropTypes.func.isRequired,
};

export default ModelsTable;
