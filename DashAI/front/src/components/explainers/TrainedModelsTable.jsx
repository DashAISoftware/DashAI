import React, { useEffect, useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Paper } from "@mui/material";
import { useSnackbar } from "notistack";
import { getExperiments as getExperimentsRequest } from "../../api/experiment";
import { getRuns as getRunsRequest } from "../../api/run";
import { formatDate } from "../../utils";

function TrainedModelsTable() {
  const { enqueueSnackbar } = useSnackbar();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  const colums = [
    {
      field: "id",
      headerName: "ID",
      minWidth: 30,
      editable: false,
    },
    {
      field: "experimentName",
      headerName: "Experiment Name",
      minWidth: 150,
      editable: false,
    },
    {
      field: "name",
      headerName: "Model Name",
      minWidth: 150,
      editable: false,
    },
    {
      field: "model_name",
      headerName: "Model",
      minWidth: 250,
      editable: false,
    },
    {
      field: "created",
      headerName: "Created",
      minWidth: 250,
      editable: false,
      type: Date,
      valueFormatter: (params) => formatDate(params.value),
    },
  ];

  const extractRows = (rawExperiments, rawRuns) => {
    let rows = [];
    // A cada run agregarlo los datos de su experimento
    rawRuns.forEach((run) => {
      let newRun = { ...run };
      const newExperiment = rawExperiments.filter(
        (experiment) => experiment.id === newRun.experiment_id,
      )[0];

      const { name: experimentName } = newExperiment;
      newRun = {
        ...newRun,
        experimentName,
      };
      rows = [...rows, newRun];
    });
    return rows;
  };

  const getModels = async () => {
    setLoading(true);
    try {
      const experiments = await getExperimentsRequest();
      const runs = await getRunsRequest();
      const rows = extractRows(experiments, runs);
      setRows(rows);
      console.log(rows);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the runs table.");
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

  useEffect(() => {
    getModels();
  }, []);

  return (
    <Paper sx={{ py: 4, px: 6 }}>
      <DataGrid
        rows={rows}
        columns={colums}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
        }}
        sortModel={[{ field: "experiment", sort: "desc" }]}
        columnVisibilityModel={{ id: false }}
        pageSize={5}
        pageSizeOptions={[5, 10]}
        disableRowSelectionOnClick
        autoHeight
        loading={loading}
      />
    </Paper>
  );
}

export default TrainedModelsTable;
