import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Alert, AlertTitle, CircularProgress, Paper } from "@mui/material";
import { DataGrid, GridToolbar } from "@mui/x-data-grid";
import { getRuns as getRunsRequest } from "../api/run";
import { useSnackbar } from "notistack";

// columns that are common to all runs
const initialColumns = [
  {
    field: "run_name",
    headerName: "Name",
    minWidth: 150,
  },
  {
    field: "model_name",
    headerName: "Model",
    minWidth: 150,
  },
  {
    field: "status",
    headerName: "Status",
    minWidth: 150,
  },
  {
    field: "created",
    headerName: "Created",
    minWidth: 180,
  },
  {
    field: "last_modified",
    headerName: "Last modified",
    type: Date,
    minWidth: 180,
  },
  {
    field: "start_time",
    headerName: "Start",
    type: Date,
    minWidth: 180,
  },
  {
    field: "end_time",
    headerName: "End",
    type: Date,
    minWidth: 180,
  },
];

// name of the properties that contain metrics in the run object
const resultsProperties = [
  "train_metrics",
  "test_metrics",
  "validation_metrics",
  "parameters",
];

// function to get prefixes for the column names of each metric
const getPrefix = (property) => {
  switch (property) {
    case "train_metrics":
      return "train_";
    case "test_metrics":
      return "test_";
    case "validation_metrics":
      return "val_";
    default:
      return "";
  }
};
function RunsTable({ experimentId }) {
  const { enqueueSnackbar } = useSnackbar();

  const [rows, setRows] = useState([]);
  const [columns, setColumns] = useState([]);
  const [columnGroupingModel, setColumnGroupingModel] = useState([]);
  const [columnVisibilityModel, setColumnVisibilityModel] = useState({});
  const [loading, setLoading] = useState(true);

  const preprocessData = (rawRuns) => {
    // add rows with the train, test, validation and parameters
    let rows = [];
    rawRuns.forEach((run) => {
      let newRun = { ...run };
      resultsProperties.forEach((p) => {
        Object.keys(run[p]).forEach((metric) => {
          newRun = { ...newRun, [`${getPrefix(p)}${metric}`]: run[p][metric] };
        });
      });
      rows = [...rows, newRun];
    });

    // columns associated to results
    let distinctColumns = {};
    resultsProperties.forEach((p) => {
      rawRuns.forEach((run) => {
        Object.keys(run[p]).forEach((metric) => {
          distinctColumns = {
            ...distinctColumns,
            [`${getPrefix(p)}${metric}`]: metric,
          };
        });
      });
    });

    const resultsColumns = Object.keys(distinctColumns).map((name) => {
      return { field: name };
    });
    // columns
    const columns = [...initialColumns, ...resultsColumns];

    // column grouping model, determines the groups within columns e.g "Run info", "Results"
    const columnGroupingModel = [
      { groupId: "Run info", children: [...initialColumns] },
      { groupId: "Results", children: [...resultsColumns] },
    ];

    // column visibility model, determines which columns are initially hidden
    let columnVisibilityModel = {
      last_modified: false,
      start_time: false,
      end_time: false,
    };
    Object.keys(distinctColumns).forEach((col) => {
      columnVisibilityModel = { ...columnVisibilityModel, [col]: false };
    });
    return { rows, columns, columnGroupingModel, columnVisibilityModel };
  };

  const getRuns = async () => {
    setLoading(true);
    try {
      const runs = await getRunsRequest();
      const { rows, columns, columnGroupingModel, columnVisibilityModel } =
        preprocessData(runs);
      setColumns(columns);
      setColumnGroupingModel(columnGroupingModel);
      setColumnVisibilityModel(columnVisibilityModel);
      setRows(rows);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the runs table.", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  // fetch the runs and preprocess the data for DataGrid
  useEffect(() => {
    getRuns();
  }, []);
  return (
    <Paper sx={{ py: 4, px: 4, ml: 7 }}>
      {experimentId === undefined && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <AlertTitle>No experiment selected</AlertTitle>
          Select an experiment to see the runs associated to it
        </Alert>
      )}
      {!loading ? (
        <DataGrid
          rows={
            experimentId
              ? rows.filter((run) => String(run.experiment_id) === experimentId)
              : []
          }
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: 10,
              },
            },
            columns: {
              columnVisibilityModel,
            },
          }}
          experimentalFeatures={{ columnGrouping: true }}
          columnGroupingModel={columnGroupingModel}
          slots={{
            toolbar: GridToolbar,
          }}
          pageSizeOptions={[10]}
          density="compact"
          disableRowSelectionOnClick
          autoHeight
        />
      ) : (
        <CircularProgress color="inherit" />
      )}
    </Paper>
  );
}

RunsTable.propTypes = {
  experimentId: PropTypes.string,
};

RunsTable.defaultProps = {
  experimentId: undefined,
};

export default RunsTable;
