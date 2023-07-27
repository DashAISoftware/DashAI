import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Alert, AlertTitle, CircularProgress, Paper } from "@mui/material";
import { DataGrid, GridActionsCellItem, GridToolbar } from "@mui/x-data-grid";
import { getRuns as getRunsRequest } from "../../api/run";
import { getComponents as getComponentsRequest } from "../../api/component";
import { getExperimentById } from "../../api/experiment";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router-dom";
import QueryStatsIcon from "@mui/icons-material/QueryStats";
import { getRunStatus } from "../../utils/runStatus";
import { formatDate } from "../../utils/index";

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
    type: Date,
    minWidth: 140,
    valueFormatter: (params) => formatDate(params.value),
  },
  {
    field: "last_modified",
    headerName: "Last modified",
    type: Date,
    minWidth: 140,
    valueFormatter: (params) => formatDate(params.value),
  },
  {
    field: "start_time",
    headerName: "Start",
    type: Date,
    minWidth: 140,
    valueFormatter: (params) => formatDate(params.value),
  },
  {
    field: "end_time",
    headerName: "End",
    type: Date,
    minWidth: 140,
    valueFormatter: (params) => formatDate(params.value),
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

  const [rows, setRows] = useState([]);
  const [columns, setColumns] = useState([]);
  const [columnGroupingModel, setColumnGroupingModel] = useState([]);
  const [columnVisibilityModel, setColumnVisibilityModel] = useState({});
  const [loading, setLoading] = useState(false);

  const actionsColumns = [
    {
      field: "actions",
      type: "actions",
      minWidth: 80,
      getActions: (params) => [
        <GridActionsCellItem
          key="specific-results-button"
          icon={<QueryStatsIcon />}
          label="Run Results"
          onClick={() =>
            navigate(
              `/app/results/experiments/${experimentId}/runs/${params.id}`,
            )
          }
          sx={{ color: "primary.main" }}
        />,
      ],
    },
  ];

  const extractRows = (rawRuns) => {
    let rows = [];
    rawRuns.forEach((run) => {
      let newRun = { ...run };
      runObjectProperties.forEach((p) => {
        // adds its corresponding prefix to the metric name (e.g. train_F1) and
        // if the metric value is a number, it is rounded to two decimal places.
        Object.keys(run[p] ?? {}).forEach((metric) => {
          newRun = {
            ...newRun,
            [`${getPrefix(p)}${metric}`]:
              typeof run[p][metric] === "number"
                ? run[p][metric].toFixed(2)
                : run[p][metric],
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
        { field: `train_${metric.name}` },
        { field: `test_${metric.name}` },
        { field: `val_${metric.name}` },
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
      { groupId: "Actions", children: [...actionsColumns] },
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
      if (col.field.includes("test")) {
        return; // skip this iteration and proceed with the next one
      }
      columnVisibilityModel = { ...columnVisibilityModel, [col.field]: false };
    });

    const columns = [
      ...actionsColumns,
      ...initialColumns,
      ...metrics,
      ...parameters,
    ];

    return { columns, columnGroupingModel, columnVisibilityModel };
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
      const rowsWithStringStatus = rows.map((run) => {
        return { ...run, status: getRunStatus(run.status) };
      });
      const { columns, columnGroupingModel, columnVisibilityModel } =
        extractColumns(metrics, runs);
      setRows(rowsWithStringStatus);
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
        width: "80vw",
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
            "& .MuiDataGrid-row:hover": {},
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
