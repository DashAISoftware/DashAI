import React, { useState } from "react";
import ItemSelectorWithDescriptionContainer from "./ItemSelectorWithDescriptionContainer";
import useTasks from "../../hooks/useTasks";
import PropTypes from "prop-types";

function TaskItemSelectorWithDescription({ defaultTask, onSelectedTask }) {
  const [selectedTask, setSelectedTask] = useState({});
  const { tasks, loading } = useTasks({
    onSuccess: (tasks) => {
      if (typeof defaultTask === "string" && defaultTask !== "") {
        const previouslySelectedTask =
          tasks.find((task) => task.name === defaultTask) || {};
        setSelectedTask(previouslySelectedTask);
      }
    },
  });

  const descriptionTitle = "Select a task to see the description.";

  const handleSelectedTask = (task) => {
    setSelectedTask(task);
    onSelectedTask(task);
  };

  return (
    <ItemSelectorWithDescriptionContainer
      itemsList={tasks}
      setSelectedItem={handleSelectedTask}
      selectedItemName={selectedTask?.name}
      title={selectedTask?.name || descriptionTitle}
      description={
        selectedTask.description || selectedTask?.schema?.description
      }
      images={selectedTask?.schema?.images}
      disabled={loading}
    />
  );
}

TaskItemSelectorWithDescription.propTypes = {
  defaultTask: PropTypes.string,
  onSelectedTask: PropTypes.func,
};

export default TaskItemSelectorWithDescription;
