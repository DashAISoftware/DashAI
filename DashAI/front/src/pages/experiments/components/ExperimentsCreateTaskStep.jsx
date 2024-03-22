import PropTypes from "prop-types";
import React from "react";

import TaskItemSelectorWithDescription from "../../../components/shared/TaskItemSelectorWithDescription";
import ExperimentsCreateTaskStepLayout from "./ExperimentsCreateTaskStepLayout";

const MAX_NAME_LENGTH = 4;

function ExperimentsCreateTaskStep({ newExp, setNewExp, setNextEnabled }) {
  // experiment name state

  const isValidName =
    typeof newExp.name === "string" && newExp.name.length >= MAX_NAME_LENGTH;

  const handleNameInputChange = (event) => {
    const name = event.target.value;
    setNewExp({ ...newExp, name });
    if (newExp?.task_name && name.length >= MAX_NAME_LENGTH) {
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  };

  const onSelectedTask = (selectedTask) => {
    if (selectedTask && "name" in selectedTask) {
      setNewExp({
        ...newExp,
        task_name: selectedTask.name,
        dataset: null,
        runs: [],
      });
      if (isValidName) {
        setNextEnabled(true);
      }
    }
  };

  return (
    <ExperimentsCreateTaskStepLayout
      inputProps={{
        value: newExp.name,
        error: !isValidName && (newExp.name !== "" || newExp?.task_name),
        onChange: handleNameInputChange,
      }}
    >
      <TaskItemSelectorWithDescription
        defaultTask={newExp.task_name}
        onSelectedTask={onSelectedTask}
      />
    </ExperimentsCreateTaskStepLayout>
  );
}

ExperimentsCreateTaskStep.propTypes = {
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

export default ExperimentsCreateTaskStep;
