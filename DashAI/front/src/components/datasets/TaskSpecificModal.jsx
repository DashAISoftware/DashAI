import React from "react";
import PropTypes from "prop-types";
import SelectTaskStep from "./SelectTaskStep";
import SelectDataloaderStep from "./SelectDataloaderStep";
import ConfigureAndUploadDataset from "./ConfigureAndUploadDataset";


/**
 * This component renders a modal that takes the user through the process of uploading a new dataset.
 * @param {bool} open true to open the modal, false to close it
 * @param {function} setOpen function to modify the value of open
 * @param {function} updateDatasets function to update the datasets table, it is used when the modal closes
 */
function TaskSpecificModal({ newDataset, setNewDataset, formSubmitRef, activeStep, setNextEnabled }) {
  return (
    <>
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
      </>
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
