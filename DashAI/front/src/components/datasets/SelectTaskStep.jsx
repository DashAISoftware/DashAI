import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";
import { getComponents as getComponentsRequest } from "../../api/component";
import ItemSelectorWithInfo from "../custom/ItemSelectorWithInfo";
import { DialogContentText, Grid } from "@mui/material";

/**
 * This component renders a list of tasks and allows the user to select one.
 * @param {object} newDataset An object that stores all the important states for the dataset modal.
 * @param {function} setNewDataset function that modifies newDataset state
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the dataset modal.
 */
function SelectTaskStep({ newDataset, setNewDataset, setNextEnabled }) {
  const { enqueueSnackbar } = useSnackbar();

  const [tasks, setTasks] = useState([]);
  const [selectedTask, setSelectedTask] = useState({});
  const [loading, setLoading] = useState(true);

  const getTasks = async () => {
    setLoading(true);
    try {
      const tasks = await getComponentsRequest({ selectTypes: ["Task"] });
      setTasks(tasks);
      // If there was a previously selected task, it is used as the initial value for the task.
      if (newDataset.task_name !== "") {
        const previouslySelectedTask =
          tasks.find((task) => task.name === newDataset.task_name) || {};
        setSelectedTask(previouslySelectedTask);
      }
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain available tasks");
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

  // updates the modal state with the name of the task that is selected by the user
  useEffect(() => {
    if (selectedTask && Object.keys(selectedTask).length === 0) {
      setNewDataset({ ...newDataset, task_name: "" });
    } else if (selectedTask && "name" in selectedTask) {
      setNewDataset({ ...newDataset, task_name: selectedTask.name });
      setNextEnabled(true);
    }
  }, [selectedTask]);

  // fetches the available tasks
  useEffect(() => {
    getTasks();
  }, []);

  return (
    <Grid
      container
      direction="column"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={2}
    >
      {/* Title */}
      <Grid item>
        <DialogContentText sx={{ mb: 3 }}>{`Select a task`}</DialogContentText>
      </Grid>
      {/* List of tasks  */}
      <Grid item>
        {!loading && (
          <ItemSelectorWithInfo
            itemsList={tasks}
            selectedItem={selectedTask}
            setSelectedItem={setSelectedTask}
          />
        )}
      </Grid>
    </Grid>
  );
}

SelectTaskStep.propTypes = {
  newDataset: PropTypes.shape({
    task_name: PropTypes.string,
    dataloader_name: PropTypes.string,
  }).isRequired,
  setNewDataset: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default SelectTaskStep;
