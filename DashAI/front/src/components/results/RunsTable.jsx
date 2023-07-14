import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Alert, AlertTitle, CircularProgress, Paper } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { DataGrid, GridToolbar } from "@mui/x-data-grid";
import { getRuns as getRunsRequest } from "../../api/run";
import { getComponents as getComponentsRequest } from "../../api/component";
import { getExperimentById } from "../../api/experiment";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router-dom";

// columns that are common to all runs
const initialColumns = [
  {
    field: "name",
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

// name of the properties in the run object that contain objects
const runObjectProperties = [
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
/**
 * This component renders a table that contains the runs associated to an experiment.
 * @param {string} experimentId id of the experiment whose runs the user wants to analyze.
 */
function RunsTable({ experimentId }) {
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const theme = useTheme();

  const [rows, setRows] = useState([]);
  const [columns, setColumns] = useState([]);
  const [columnGroupingModel, setColumnGroupingModel] = useState([]);
  const [columnVisibilityModel, setColumnVisibilityModel] = useState({});
  const [loading, setLoading] = useState(false);

  const extractRows = (rawRuns) => {
    let rows = [];
    rawRuns.forEach((run) => {
      let newRun = { ...run };
      runObjectProperties.forEach((p) => {
        Object.keys(run[p] ?? {}).forEach((metric) => {
          newRun = {
            ...newRun,
            [`${getPrefix(p)}${metric}`]: run[p][metric],
          };
        });
      });
      rows = [...rows, newRun];
    });
    return rows;
  };

  const extractColumns = (rawMetrics, rawRuns) => {
    // extract metrics
    let metrics = [];
    for (const metric of rawMetrics) {
      metrics = [
        ...metrics,
        { field: `train_ ${metric.name}` },
        { field: `test_ ${metric.name}` },
        { field: `val_ ${metric.name}` },
      ];
    }

    // extract parameters
    let distinctParameters = {};
    for (const run of rawRuns) {
      distinctParameters = { ...distinctParameters, ...run.parameters };
    }
    const parameters = Object.keys(distinctParameters).map((name) => {
      return { field: name };
    });

    // column grouping
    const columnGroupingModel = [
      { groupId: "Info", children: [...initialColumns] },
      { groupId: "Metrics", children: [...metrics] },
      { groupId: "Parameters", children: [...parameters] },
    ];

    // column visibility
    let columnVisibilityModel = {
      last_modified: false,
      start_time: false,
      end_time: false,
    };
    [...metrics, ...parameters].forEach((col) => {
      columnVisibilityModel = { ...columnVisibilityModel, [col.field]: false };
    });

    const columns = [...initialColumns, ...metrics, ...parameters];

    return { columns, columnGroupingModel, columnVisibilityModel };
  };

  const handleRowDoubleClick = (params) => {
    navigate(`/app/results/experiments/${experimentId}/runs/${params.id}`);
  };

  const getRuns = async () => {
    setLoading(true);
    try {
      const runs = await getRunsRequest(experimentId);
      const experiment = await getExperimentById(experimentId);
      const metrics = await getComponentsRequest({
        selectTypes: ["Metric"],
        relatedComponent: experiment.task_name,
      });
      const rows = extractRows(runs);
      const { columns, columnGroupingModel, columnVisibilityModel } =
        extractColumns(metrics, runs);
      setRows(rows);
      setColumns(columns);
      setColumnGroupingModel(columnGroupingModel);
      setColumnVisibilityModel(columnVisibilityModel);
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

  // fetch the runs and preprocess the data for DataGrid
  useEffect(() => {
    if (experimentId !== undefined) {
      getRuns();
    }
  }, [experimentId]);
  return (
    <Paper
      sx={{
        p: 4,
        [theme.breakpoints.up("xs")]: { ml: 8 },
        [theme.breakpoints.up("sm")]: { ml: 12 },
        [theme.breakpoints.up("md")]: { ml: 20 },
        [theme.breakpoints.up("lg")]: { width: "80vw", ml: 15 },
        [theme.breakpoints.up("xl")]: { width: "80vw", ml: 10 },
      }}
    >
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
          onRowDoubleClick={handleRowDoubleClick}
          pageSizeOptions={[10]}
          density="compact"
          disableRowSelectionOnClick
          autoHeight
          sx={{
            // disable cell selection style
            ".MuiDataGrid-cell:focus": {
              outline: "none",
            },
            // pointer cursor on ALL rows
            "& .MuiDataGrid-row:hover": {
              cursor: "pointer",
            },
          }}
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
