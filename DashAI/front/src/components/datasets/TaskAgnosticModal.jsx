import React from "react";
import PropTypes from "prop-types";
import SelectDataloaderStep from "./SelectDataloaderStep";
import ConfigureAndUploadDataset from "./ConfigureAndUploadDataset";

/**
 * This component renders a modal that takes the user through the process of uploading a new dataset.
 * @param {object} newDataset An object that stores all the important states for the dataset modal.
 * @param {function} setNewDataset function that modifies newDataset state
 * @param {object} formSubmitRef useRef to trigger form submit from outside "ParameterForm" component
 * @param {number} activeStep declares the current step of the flow
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the modal.
 */
function TaskAgnosticModal({
  newDataset,
  setNewDataset,
  formSubmitRef,
  activeStep,
  setNextEnabled,
}) {
  return (
    <React.Fragment>
      {/* Step 1: select dataloader */}
      {activeStep === 1 && (
        <SelectDataloaderStep
          newDataset={newDataset}
          setNewDataset={setNewDataset}
          setNextEnabled={setNextEnabled}
          taskType={1}
        />
      )}
      {/* Step 2: Configure dataloader and upload file */}
      {activeStep === 2 && (
        <ConfigureAndUploadDataset
          newDataset={newDataset}
          setNewDataset={setNewDataset}
          setNextEnabled={setNextEnabled}
          formSubmitRef={formSubmitRef}
        />
      )}
    </React.Fragment>
  );
}
TaskAgnosticModal.propTypes = {
  newDataset: PropTypes.bool.isRequired,
  setNewDataset: PropTypes.func.isRequired,
  formSubmitRef: PropTypes.func.isRequired,
  activeStep: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default TaskAgnosticModal;
