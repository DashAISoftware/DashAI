import React, { useState, useEffect } from "react";
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
// import SchemaList from "../SchemaList";
import { getTasks as getTasksRequest } from "../../api/tasks";
import { useSnackbar } from "notistack";

function SelectTaskStep() {
  const { enqueueSnackbar } = useSnackbar();

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [displayTasks, setDisplayTasks] = React.useState(tasks.map(() => true));
  const [searchField, setSearchField] = React.useState("");
  const [selectedTaskIndex, setSelectedTaskIndex] = React.useState(null);

  const getTasks = async () => {
    setLoading(true);
    try {
      const tasks = await getTasksRequest();
      setTasks(tasks);
      setDisplayTasks(tasks.map(() => true));
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

  // Fetch tasks when the component is mounting
  useEffect(() => {
    getTasks();
  }, []);

  const handleListItemClick = (event, index) => {
    setSelectedTaskIndex(index);
  };

  const handleClearSearchField = (event) => {
    setSearchField("");
    setDisplayTasks(tasks.map(() => true));
  };

  const handleSearchFieldChange = (event) => {
    setSearchField(event.target.value);
    setDisplayTasks(
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
                  defaultValue=""
                  fullWidth
                  label="Search task"
                  type="search"
                  variant="standard"
                  value={searchField}
                  onChange={handleSearchFieldChange}
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
                    {displayTasks}
                    <ListItem
                      key={`task-list-button-${task.name}`}
                      disablePadding
                      sx={{ display: displayTasks[index] ? "show" : "none" }}
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
                  <Typography variant="h6">
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

SelectTaskStep.propTypes = {};

export default SelectTaskStep;
