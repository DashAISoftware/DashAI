import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import PropTypes from "prop-types";
import { Container } from "react-bootstrap";
import ExperimentsTable from "../components/ExperimentsTable";
import SchemaList from "../components/SchemaList";
import { rows } from "../example_data/experiments";
import { Typography } from "@mui/material";

function DataloaderModal({
  selectedTask,
  showModal,
  handleModal,
  setShowTasks,
  outputData,
}) {
  /*
    This modal shows the list of dataloaders
  */
  useEffect(() => {
    handleModal(true);
  }, []);
  const handleBack = () => {
    handleModal(false);
    setShowTasks(true);
  };
  return (
    <SchemaList
      schemaType="task"
      schemaName={selectedTask}
      itemsName="way to upload your data"
      description="How do you want to load your data?"
      showModal={showModal}
      handleModalClose={() => handleModal(false)}
      handleBack={handleBack}
      outputData={outputData}
    />
  );
}

function Home() {
  const [showTasks, setShowTasks] = useState(false);
  const [selectedTask, setSelectedTask] = useState();
  const [showDataloaders, setShowDataloaders] = useState(false);
  const [selectedDataloader, setSelectedDataloader] = useState();
  const navigate = useNavigate();
  const goToUpload = () => {
    navigate("/app/data", {
      state: { dataloader: selectedDataloader, taskName: selectedTask },
    });
  };
  useEffect(() => {
    if (selectedDataloader !== undefined) {
      goToUpload();
    }
  }, [selectedDataloader]);
  const location = useLocation();
  const task = location.state?.task;
  window.history.replaceState({}, document.title);
  useEffect(() => {
    setSelectedTask(task);
  }, []);

  // const [experimentsInTable, setExperimentsInTable] = useState(rows);
  // const removeExperimentFactory = (index) => {
  //   console.log(index);
  //   const experimentsArray = [...experimentsInTable];
  //   experimentsArray.splice(index, 1);
  //   setExperimentsInTable(experimentsArray);
  // };
  const handleNewExperiment = () => {
    /* Show the task list and reset the selected option */
    setSelectedTask(undefined);
    setShowTasks(!showTasks);
  };
  return (
    <Container>
      {/* Title */}
      <Typography variant="h3" component="h1" sx={{ mb: 6 }}>
        Welcome to DashAI!
      </Typography>

      {/* Experiment table */}
      <ExperimentsTable
        initialRows={rows}
        handleNewExperiment={handleNewExperiment}
      />

      <SchemaList
        schemaType="task"
        schemaName="tasks"
        itemsName="task"
        description="What do you want to do today?"
        showModal={showTasks}
        handleModalClose={() => setShowTasks(false)}
        handleBack={() => setShowTasks(false)}
        outputData={setSelectedTask}
      />
      {selectedTask !== undefined ? (
        <DataloaderModal
          selectedTask={selectedTask}
          showModal={showDataloaders}
          handleModal={setShowDataloaders}
          setShowTasks={setShowTasks}
          outputData={setSelectedDataloader}
        />
      ) : null}
    </Container>
  );
}

DataloaderModal.propTypes = {
  selectedTask: PropTypes.string.isRequired,
  showModal: PropTypes.bool.isRequired,
  handleModal: PropTypes.func.isRequired,
  setShowTasks: PropTypes.func.isRequired,
  outputData: PropTypes.func.isRequired,
};
export default Home;
