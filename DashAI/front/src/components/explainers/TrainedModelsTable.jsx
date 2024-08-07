import React, { useEffect, useState } from "react";
import { DataGrid, GridActionsCellItem, GridToolbar } from "@mui/x-data-grid";
import { Grid, MenuItem, Paper, TextField, Typography } from "@mui/material";
import QueryStatsIcon from "@mui/icons-material/QueryStats";
import { useNavigate } from "react-router-dom";
import { useSnackbar } from "notistack";
import { getExperiments as getExperimentsRequest } from "../../api/experiment";
import { getRuns as getRunsRequest } from "../../api/run";
import { formatDate } from "../../utils";
import { getComponents } from "../../api/component";
import TimestampWrapper from "../shared/TimestampWrapper";
import { TIMESTAMP_KEYS } from "../../constants/timestamp";

function TrainedModelsTable() {
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState("All Tasks");
  const [tasks, setTasks] = useState([]);
  const [originalRows, setOriginalRows] = useState([]);

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
      minWidth: 170,
      editable: false,
    },
    {
      field: "name",
      headerName: "Model Name",
      minWidth: 170,
      editable: false,
    },
    {
      field: "model_name",
      headerName: "Model",
      minWidth: 170,
      editable: false,
    },
    {
      field: "created",
      headerName: "Created",
      minWidth: 170,
      editable: false,
      type: Date,
      valueFormatter: (params) => formatDate(params.value),
    },
    {
      field: "actions",
      headerName: "Dashboard",
      headerWidth: 1,
      type: "actions",
      mindWidth: 170,
      getActions: (params) => [
        <TimestampWrapper eventName={TIMESTAMP_KEYS.explainer.enterDashboard}>
          <GridActionsCellItem
            key="specific-results-button"
            icon={<QueryStatsIcon />}
            label="Run Results"
            onClick={() =>
              navigate(`/app/explainers/runs/${params.row.id}`, {
                state: {
                  modelName: params.row.name,
                },
              })
            }
            sx={{ color: "primary.main" }}
          />
        </TimestampWrapper>,
      ],
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

      const {
        name: experimentName,
        dataset_id: datasetId,
        task_name: taskName,
      } = newExperiment;
      newRun = {
        ...newRun,
        experimentName,
        datasetId,
        taskName,
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
      const filteredRows = rows.filter((row) => row.status === 3);
      setOriginalRows(filteredRows);
      setRows(filteredRows);
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

  const getTasks = async () => {
    setLoading(true);
    try {
      const tasks = await getComponents({ selectTypes: ["Task"] });
      setTasks(tasks);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the tasks.");
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
    getTasks();
  }, []);

  const taskFilter = (event) => {
    const taskName = event.target.value;
    setSelectedTask(taskName);
    if (taskName === "All Tasks") {
      setRows(originalRows);
    } else {
      let newRows = [];
      originalRows.forEach((row) => {
        if (row.taskName === taskName) {
          newRows = [...newRows, row];
        }
      });
      setRows(newRows);
    }
  };

  return (
    <Paper sx={{ py: 4, px: 6 }}>
      <Grid container spacing={2}>
        <Grid item xs={4}>
          <Typography variant="h6" component="h2" sx={{ mb: 1 }}>
            Models
          </Typography>
        </Grid>
        <Grid item xs={4}></Grid>
        <Grid item xs={4}>
          <TextField
            sx={{ mb: 1, mt: -1 }}
            select
            label="Select Task"
            value={selectedTask}
            onChange={taskFilter}
            fullWidth
          >
            <MenuItem key={"Wildcard"} value={"All Tasks"}>
              All tasks
            </MenuItem>
            {tasks.map((task) => (
              <MenuItem key={task.name} value={task.name}>
                {task.name}
              </MenuItem>
            ))}
          </TextField>
        </Grid>
      </Grid>
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
        slots={{
          toolbar: GridToolbar,
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
