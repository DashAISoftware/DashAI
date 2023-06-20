import React, { useState, useRef } from "react";
import PropTypes from "prop-types";
/* import {
  Dialog,
  DialogTitle,
  DialogContent,
  Stepper,
  Step,
  DialogActions,
  ButtonGroup,
  Button,
  Grid,
  Typography,
  StepButton,
} from "@mui/material"; */
import SelectTaskStep from "./SelectTaskStep";
import SelectDataloaderStep from "./SelectDataloaderStep";
import ConfigureAndUploadDataset from "./ConfigureAndUploadDataset";
/* import { useSnackbar } from "notistack";
import { uploadDataset as uploadDatasetRequest } from "../../api/datasets"; */

/* const steps = [
  { name: "selectTask", label: "Select Task" },
  { name: "selectDataloader", label: "Select a way to upload" },
  { name: "uploadDataset", label: "Configure and upload your dataset" },
];
*/
const defaultNewDataset = {
  task_name: "",
  dataloader: "",
  file: null,
  url: "",
  params: {},
}; 

/**
 * This component renders a modal that takes the user through the process of uploading a new dataset.
 * @param {bool} open true to open the modal, false to close it
 * @param {function} setOpen function to modify the value of open
 * @param {function} updateDatasets function to update the datasets table, it is used when the modal closes
 */
function TaskSpecificModal({ open, setOpen, updateDatasets, activeStep, setNextEnabled }) {
  const [newDataset, setNewDataset] = useState(defaultNewDataset);
  const formSubmitRef = useRef(null);
  // const { enqueueSnackbar } = useSnackbar();
/* 
  const handleSubmitNewDataset = async () => {
    try {
      const formData = new FormData();
      const dataloaderName = newDataset.params.dataloader_params.name;

      formData.append(
        "params",
        JSON.stringify({
          ...newDataset.params,
          dataset_name:
            dataloaderName !== "" ? dataloaderName : newDataset.file.name,
        }),
      );
      formData.append("url", ""); // TODO: url handling
      formData.append("file", newDataset.file);
      await uploadDatasetRequest(formData);
      enqueueSnackbar("Dataset uploaded successfully", {
        variant: "success",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
    } catch (error) {
      console.error(error);
      enqueueSnackbar("Error when trying to upload the dataset.", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
    }
  };

  const handleCloseDialog = () => {
    setActiveStep(0);
    setNewDataset(defaultNewDataset);
    setNextEnabled(false);
    setTimeout(() => updateDatasets());
    setOpen(false);
  };

  const handleStepButton = (stepIndex) => () => {
    setActiveStep(stepIndex);
  };

  const handleNextButton = () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1);
      setNextEnabled(false);
    } else {
      // trigger dataloader form submit
      formSubmitRef.current.handleSubmit();
    }
  };

  const handleBackButton = () => {
    if (activeStep === 0) {
      handleCloseDialog();
    } else {
      setActiveStep(activeStep - 1);
    }
  };

  // submits the new dataset when it has all necessary data
  useEffect(() => {
    if (newDataset.file !== null && Object.keys(newDataset.params).length > 0) {
      handleSubmitNewDataset();
      handleCloseDialog();
    }
  }, [newDataset]);
 */
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
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  updateDatasets: PropTypes.func.isRequired,
  activeStep: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default TaskSpecificModal;
