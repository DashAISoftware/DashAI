import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";

import { CircularProgress, Grid, TextField, Typography } from "@mui/material";
import { useSnackbar } from "notistack";

import { getComponents as getComponentsRequest } from "../../api/component";

import ItemSelectorWithInfo from "../custom/ItemSelectorWithInfo";

function SetNameAndTaskStep({ newExp, setNewExp, setNextEnabled }) {
  const { enqueueSnackbar } = useSnackbar();

  const [loading, setLoading] = useState(false);

  // experiment name state
  const [nModifications, setNModifications] = useState(0);
  const [expNameOk, setExpNameOk] = useState(false);
  const [expNameError, setExpNameError] = useState(false);

  // tasks state
  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState({});
  const [taskNameOk, setTaskNameOk] = useState(false);

  const getTasks = async () => {
    setLoading(true);
    try {
      const tasks = await getComponentsRequest({ selectTypes: ["Task"] });
      setTasks(tasks);
      // autoselect task and if some task was selected previously.
      if (typeof newExp.task_name === "string" && newExp.task_name !== "") {
        const previouslySelectedTask =
          tasks.find((task) => task.name === newExp.task_name) || {};
        setSelectedTask(previouslySelectedTask);
      }
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the task list.");
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

  // when a task is selected it synchronizes the value of the selected task (object) with the value in newExp (string)
  useEffect(() => {
    if (selectedTask && "name" in selectedTask) {
      setNewExp({
        ...newExp,
        task_name: selectedTask.name,
        dataset: null,
        runs: [],
      });
      setTaskNameOk(true);
    }
  }, [selectedTask]);

  // on mount, fetch tasks.
  useEffect(() => {
    getTasks();
  }, []);

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
          {/* Tasks list and description */}
          {!loading ? (
            <ItemSelectorWithInfo
              itemsList={tasks}
              selectedItem={selectedTask}
              setSelectedItem={setSelectedTask}
            />
          ) : (
            <CircularProgress color="inherit" />
          )}
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
