import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import ItemSelectorWithInfo from "../custom/ItemSelectorWithInfo";
import { DialogContentText, Grid } from "@mui/material";

/**
 * This component renders a list of tasks and allows the user to select one.
 * @param {number} setTaskType declares task type chosen
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the dataset modal.
 */
function SelectDatasetStep({ setTaskType, setNextEnabled }) {
  const [selectedTaskType, setSelectedTaskType] = useState({});

  const taskTypeOptions = [
    { name: "Task Specific", type: 1, description: "Choose a task and upload a known dataset." },
    { name: "Task Agnostic", type: 2, description: "Upload and transform a new dataset in Data Studio then choose a matching task."}
    ];

  // updates the modal state with the name of the task that is selected by the user
  useEffect(() => {
    if (selectedTaskType && Object.keys(selectedTaskType).length === 0) {
      setTaskType(0);
    } else if (selectedTaskType) {
      setTaskType(selectedTaskType.type)
      setNextEnabled(true);
    }
  }, [selectedTaskType]);

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
        <DialogContentText sx={{ mb: 3 }}>{`Select how to upload a new dataset`}</DialogContentText>
      </Grid>
      {/* List of tasks  */}
      <Grid item>
          <ItemSelectorWithInfo
            itemsList={taskTypeOptions}
            selectedItem={selectedTaskType}
            setSelectedItem={setSelectedTaskType}
          />
      </Grid>
    </Grid>
  );
}

SelectDatasetStep.propTypes = {
  setTaskType: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default SelectDatasetStep;
