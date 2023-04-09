import React from "react";
import {
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
import { tasks as initialTasks } from "../../example_data/tasks";

function SelectTaskStep() {
  const [tasks] = React.useState(initialTasks);
  const [displayTasks, setDisplayTasks] = React.useState(tasks.map(() => true));
  const [searchField, setSearchField] = React.useState("");
  const [selectedIndex, setSelectedIndex] = React.useState(null);

  const handleListItemClick = (event, index) => {
    setSelectedIndex(index);
  };

  const handleClearSearchField = (event) => {
    setSearchField("");
    setDisplayTasks(tasks);
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
              {tasks.map((task, index) => {
                return (
                  <ListItem
                    key={`task-list-button-${task.name}`}
                    disablePadding
                    sx={{ display: displayTasks[index] ? "show" : "none" }}
                  >
                    <ListItemButton
                      selected={selectedIndex === index}
                      onClick={(event) => handleListItemClick(event, index)}
                    >
                      <ListItemText primary={task.name} />
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </List>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper
            variant="outlined"
            sx={{ p: 2, display: "flex" }}
            elevation={10}
          >
            <Typography>Some description...</Typography>
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
}

SelectTaskStep.propTypes = {};

export default SelectTaskStep;
