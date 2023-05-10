import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

import {
  CircularProgress,
  Grid,
  IconButton,
  InputAdornment,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { Clear as ClearIcon } from "@mui/icons-material";
import { useSnackbar } from "notistack";

import { getTasks as getTasksRequest } from "../../api/task";

function SetNameAndTaskStep({ newExp, setNewExp, setNextEnabled }) {
  const { enqueueSnackbar } = useSnackbar();

  const [loading, setLoading] = useState(false);

  // experiment name state
  const [nModifications, setNModifications] = useState(0);
  const [expNameOk, setExpNameOk] = useState(false);
  const [expNameError, setExpNameError] = useState(false);

  // tasks state
  const [tasks, setTasks] = useState([]);
  const [displayedTasks, setDisplayedTasks] = useState(tasks.map(() => true));
  const [searchField, setSearchField] = useState("");
  const [selectedTaskIndex, setSelectedTaskIndex] = useState(null);
  const [taskNameOk, setTaskNameOk] = useState(false);

  const getTasks = async () => {
    setLoading(true);
    try {
      const tasks = await getTasksRequest();
      setTasks(tasks);
      setDisplayedTasks(tasks.map(() => true));
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the task list.", {
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

  const handleNameInputChange = (event) => {
    setNewExp({ ...newExp, name: event.target.value });
    setNModifications(nModifications + 1);

    if (nModifications + 1 >= 4) {
      if (event.target.value.length < 4) {
        setExpNameError(true);
        setExpNameOk(false);
      } else {
        setExpNameError(false);
        setExpNameOk(true);
      }
    }
  };

  const handleTasksListItemClick = (event, index) => {
    setSelectedTaskIndex(index);
    setNewExp({
      ...newExp,
      task_name: tasks[index].class,
      dataset: null,
      runs: [],
    });
    setTaskNameOk(true);
  };

  const handleClearSearchField = (event) => {
    setSearchField("");
    setDisplayedTasks(tasks.map(() => true));
  };

  const handleSearchFieldChange = (event) => {
    setSearchField(event.target.value);
    setDisplayedTasks(
      tasks.map((val) => val.name.toLowerCase().includes(event.target.value)),
    );
  };

  // on mount, fetch tasks.
  useEffect(() => {
    getTasks();
  }, []);

  // after task fetch, autoselect task and if some task was selected previously.
  useEffect(() => {
    if (typeof newExp.task_name === "string" && newExp.task_name !== "") {
      const tasksEqualToExpTask = tasks.map(
        (task) => task.class === newExp.task_name,
      );
      const indexOfTrue = tasksEqualToExpTask.indexOf(true);
      if (indexOfTrue !== -1) {
        setTaskNameOk(true);
        setSelectedTaskIndex(indexOfTrue);
      }
    }
  }, [tasks]);

  // in mount, set name ok if the experiment has already a valid name.
  useEffect(() => {
    if (typeof newExp.name === "string" && newExp.name.length >= 4) {
      setExpNameOk(true);
      setNModifications(4);
    }
  }, []);

  // enable next button y nameOk and taskOk are true.
  useEffect(() => {
    if (expNameOk && taskNameOk) {
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [expNameOk, taskNameOk]);

  return (
    <Grid
      container
      direction="row"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={2}
    >
      {/* Set Name subcomponent */}
      <Grid item xs={12}>
        <Typography variant="subtitle1" component="h3" sx={{ mb: 3 }}>
          Enter a name and select the task for the new experiment
        </Typography>

        <TextField
          id="experiment-name-input"
          label="Experiment name"
          value={newExp.name}
          fullWidth
          onChange={handleNameInputChange}
          sx={{ mb: 2 }}
          error={expNameError}
          helperText="The experiment name must have at least 4 alphanumeric characters."
        />
      </Grid>

      {/* Tasks Subcomponent */}
      <Grid item xs={12}>
        <Grid container spacing={1}>
          {/* Tasks list  */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, pt: 0 }} square>
              <List sx={{ width: "100%" }} dense>
                <ListItem disablePadding>
                  <TextField
                    id="task-search-input"
                    label="Search task"
                    type="search"
                    variant="standard"
                    value={searchField}
                    onChange={handleSearchFieldChange}
                    fullWidth
                    size="small"
                    sx={{ mb: 2 }}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment
                          position="end"
                          onClick={handleClearSearchField}
                        >
                          <IconButton>
                            <ClearIcon />
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                </ListItem>

                {/* Loading item (activated when useEffect is requesting the task list) */}
                {loading && (
                  <ListItem sx={{ display: "flex", justifyContent: "center" }}>
                    <CircularProgress color="inherit" />
                  </ListItem>
                )}
                {/* Rendered tasks */}
                {tasks.map((task, index) => {
                  return (
                    <div key={index}>
                      {/* {JSON.stringify(task)} */}
                      {displayedTasks}
                      <ListItem
                        key={`task-list-button-${task.name}`}
                        disablePadding
                        sx={{
                          display: displayedTasks[index] ? "show" : "none",
                        }}
                      >
                        <ListItemButton
                          selected={selectedTaskIndex === index}
                          onClick={(event) =>
                            handleTasksListItemClick(event, index)
                          }
                        >
                          <ListItemText primary={task.name} />
                        </ListItemButton>
                      </ListItem>
                    </div>
                  );
                })}
              </List>
            </Paper>
          </Grid>

          {/* Task description */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2, height: "100%" }} square>
              <Grid
                container
                direction="row"
                justifyContent="center"
                alignContent="flex-start"
              >
                <Grid item xs={12}>
                  {selectedTaskIndex === null && (
                    <Typography variant="subtitle1">
                      Select a task to see the description.
                    </Typography>
                  )}
                </Grid>

                {selectedTaskIndex !== null && (
                  <>
                    <Grid item xs={12}>
                      <Typography variant="h6" sx={{ mb: 4 }}>
                        {tasks[selectedTaskIndex].name}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography>
                        {tasks[selectedTaskIndex].description}
                      </Typography>
                    </Grid>
                  </>
                )}
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
}

SetNameAndTaskStep.propTypes = {
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
  setNextEnabled: PropTypes.func.isRequired,
};

export default SetNameAndTaskStep;
