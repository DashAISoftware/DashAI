import React from "react";
import PropTypes from "prop-types";
import SelectTaskStep from "./SelectTaskStep";
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
function TaskSpecificModal({ newDataset, setNewDataset, formSubmitRef, activeStep, setNextEnabled }) {
  return (
    <React.Fragment>
        {/* Step 1: select task */}
        {activeStep === 1 && (
          <SelectTaskStep
            newDataset={newDataset}
            setNewDataset={setNewDataset}
            setNextEnabled={setNextEnabled}
          />
        )}
        {/* Step 2: select dataloader */}
        {activeStep === 2 && (
          <SelectDataloaderStep
            newDataset={newDataset}
            setNewDataset={setNewDataset}
            setNextEnabled={setNextEnabled}
            taskType={0}
          />
        )}
        {/* Step 3: Configure dataloader and upload file */}
        {activeStep === 3 && (
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
TaskSpecificModal.propTypes = {
  newDataset: PropTypes.bool.isRequired,
  setNewDataset: PropTypes.func.isRequired,
  formSubmitRef: PropTypes.func.isRequired,
  activeStep: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default TaskSpecificModal;
