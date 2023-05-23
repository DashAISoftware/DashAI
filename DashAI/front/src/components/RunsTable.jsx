import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { CircularProgress, Paper } from "@mui/material";
import { DataGrid, GridToolbar } from "@mui/x-data-grid";
import // cols as mlflowCols,
// rows as mlflowRows,
"../example_data/mlflowRuns";
import { getRuns as getRunsRequest } from "../api/run";
import { useSnackbar } from "notistack";

function RunsTable({ experimentId }) {
  const { enqueueSnackbar } = useSnackbar();

  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  const getRuns = async () => {
    setLoading(true);
    try {
      const runs = await getRunsRequest();
      setRows(runs);
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
      // valueFormatter: (params) => formatDate(params.value),
    },
    {
      field: "last_modified",
      headerName: "Last modified",
      type: Date,
      minWidth: 180,
      // editable: false,
      // valueFormatter: (params) => formatDate(params.value),
    },
    {
      field: "start_time",
      headerName: "Start",
      type: Date,
      minWidth: 180,
      // editable: false,
      // valueFormatter: (params) => formatDate(params.value),
    },
    {
      field: "end_time",
      headerName: "End",
      type: Date,
      minWidth: 180,
      // editable: false,
      // valueFormatter: (params) => formatDate(params.value),
    },
  ];

  const resultsColumns = [
    { field: "train_metrics" },
    { field: "test_metrics" },
    { field: "validation_metrics" },
    { field: "parameters" },
  ];

  const columns = React.useMemo(
    () => [...initialColumns, ...resultsColumns],
    [],
  );

  // fetch runs in the database
  useEffect(() => {
    getRuns();
  }, []);
  return (
    <Paper sx={{ py: 4, px: 6 }}>
      {!loading ? (
        <DataGrid
          rows={
            experimentId
              ? rows.filter((run) => String(run.experiment_id) === experimentId)
              : rows
          }
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: 10,
              },
            },
            columns: {
              columnVisibilityModel: {
                run_name: true,
                model_name: true,
              },
            },
          }}
          experimentalFeatures={{ columnGrouping: true }}
          columnGroupingModel={[
            {
              groupId: "Run info",
              children: [...initialColumns],
            },
            {
              groupId: "Results",
              children: [...resultsColumns],
            },
          ]}
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
