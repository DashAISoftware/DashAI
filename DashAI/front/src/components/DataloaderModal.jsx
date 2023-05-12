import React, { useEffect } from "react";
import PropTypes from "prop-types";
import SchemaList from "./SchemaList";

function DataloaderModal({
  selectedTask,
  showModal,
  handleModal,
  setShowTasks,
  outputData,
  setShowParams,
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
      onModalClose={() => {
        handleModal(false);
        setShowParams(true);
      }}
      onBack={handleBack}
      outputData={outputData}
    />
  );
}

DataloaderModal.propTypes = {
  selectedTask: PropTypes.string.isRequired,
  showModal: PropTypes.bool.isRequired,
  handleModal: PropTypes.func.isRequired,
  setShowTasks: PropTypes.func.isRequired,
  outputData: PropTypes.func.isRequired,
  setShowParams: PropTypes.func.isRequired,
};
export default DataloaderModal;
