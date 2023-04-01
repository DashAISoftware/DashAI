import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import PropTypes from "prop-types";
import { Container } from "react-bootstrap";
import { StyledButton } from "../styles/globalComponents";
import ExperimentsTable from "../components/ExperimentsTable";
import SchemaList from "../components/SchemaList";

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
  const toDate = (timestamp) => {
    const dateConverter = new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
    return dateConverter.format(timestamp);
  };
  const rows = [
    {
      name: "myProject",
      created: toDate(Date.now()),
      edited: toDate(Date.now()),
      taskName: "NumericClassification",
      dataset: "Iris",
    },
    {
      name: "myProject2",
      created: toDate(Date.now()),
      edited: toDate(Date.now()),
      taskName: "TextClassification",
      dataset: "twitterDataset",
    },
  ];
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
      <StyledButton
        variant="dark"
        onClick={handleNewExperiment}
        style={{ margin: "50px 0px 20px" }}
      >
        + New Experiment
      </StyledButton>
      <ExperimentsTable rows={rows} removeExperimentFactory={() => {}} />
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
