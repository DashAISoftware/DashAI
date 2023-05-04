import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

import {
  CircularProgress,
  DialogContentText,
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

function SelectTaskStep({ newExp, setNewExp, setNextEnabled }) {
  const { enqueueSnackbar } = useSnackbar();

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [displayedTasks, setDisplayedTasks] = useState(tasks.map(() => true));
  const [searchField, setSearchField] = useState("");
  const [selectedTaskIndex, setSelectedTaskIndex] = useState(null);

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

  // fetch tasks when the component is mounting
  useEffect(() => {
    getTasks();
  }, []);

  // autoselect task and enable next button if some task was selected previously.
  useEffect(() => {
    if (typeof newExp.task_name === "string" && newExp.task_name !== "") {
      setNextEnabled(true);
      const tasksEqualToNewTask = tasks.map(
        (task) => task.name === newExp.task_name
      );
      const indexOfTrue = tasksEqualToNewTask.indexOf(true);
      if (indexOfTrue !== -1) {
        setSelectedTaskIndex(indexOfTrue);
      }
    }
  }, [tasks]);

  const handleListItemClick = (event, index) => {
    setSelectedTaskIndex(index);
    setNewExp({ ...newExp, task_name: tasks[index].name });
    setNextEnabled(true);
  };

  const handleClearSearchField = (event) => {
    setSearchField("");
    setDisplayedTasks(tasks.map(() => true));
  };

  const handleSearchFieldChange = (event) => {
    setSearchField(event.target.value);
    setDisplayedTasks(
      tasks.map((val) => val.name.toLowerCase().includes(event.target.value))
    );
  };

  return (
    <Paper variant="outlined" sx={{ p: 4 }}>
      <DialogContentText
        id="new-experiment-select-task-step-dialog"
        sx={{ mb: 3 }}
      >
        <Typography>Select the task to solve in the experiment.</Typography>
      </DialogContentText>
      <Grid
        container
        direction="row"
        justifyContent="space-around"
        alignItems="stretch"
        spacing={2}
      >
        {/* Tasks list  */}
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2, pt: 0 }} elevation={10}>
            <List sx={{ width: "100%" }}>
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
                      sx={{ display: displayedTasks[index] ? "show" : "none" }}
                    >
                      <ListItemButton
                        selected={selectedTaskIndex === index}
                        onClick={(event) => handleListItemClick(event, index)}
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
          <Paper
            variant="outlined"
            sx={{ p: 2, height: "100%" }}
            elevation={10}
          >
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
    </Paper>
  );
}

SelectTaskStep.propTypes = {
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

export default SelectTaskStep;
