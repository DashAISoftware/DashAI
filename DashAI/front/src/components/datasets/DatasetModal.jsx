import React, { useState, useRef, useEffect } from "react";
import PropTypes from "prop-types";
import {
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
} from "@mui/material";
import SelectDataloaderStep from "./SelectDataloaderStep";
import ConfigureAndUploadDataset from "./ConfigureAndUploadDataset";
import { useSnackbar } from "notistack";
import { uploadDataset as uploadDatasetRequest } from "../../api/datasets";
import DatasetSummaryStep from "./DatasetSummaryStep";

const steps = [
  { name: "selectDataloader", label: "Select a way to upload" },
  { name: "uploadDataset", label: "Configure and upload your dataset" },
  { name: "datasetSummary", label: "Dataset summary" },
];

const defaultNewDataset = {
  dataloader: "",
  file: null,
  url: "",
  params: {},
};

/**
 * This component renders a modal that takes the user through the process of uploading a new dataset.
 * @param {bool} open true to open the modal, false to close it
 * @param {function} setOpen function to modify the value of open
 * @param {function} updateDatasets function to update the datasets table
 */
function DatasetModal({ open, setOpen, updateDatasets }) {
  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);
  const [newDataset, setNewDataset] = useState(defaultNewDataset);
  const [readyToUpload, setReadyToUpload] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [requestError, setRequestError] = useState(false);
  const [uploadedDataset, setUploadedDataset] = useState([]);
  const formSubmitRef = useRef(null);
  const { enqueueSnackbar } = useSnackbar();

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
      const dataset = await uploadDatasetRequest(formData);
      setUploadedDataset(dataset);
      enqueueSnackbar("Dataset uploaded successfully", { variant: "success" });
      updateDatasets();
    } catch (error) {
      console.error(error);
      setRequestError(true);
      enqueueSnackbar("Error when trying to upload the dataset.");
    } finally {
      setUploaded(true);
    }
  };
  const handleCloseDialog = () => {
    setActiveStep(0);
    setNewDataset(defaultNewDataset);
    setNextEnabled(false);
    setOpen(false);
  };

  const handleStepButton = (stepIndex) => () => {
    setActiveStep(stepIndex);
  };

  const handleNextButton = () => {
    if (activeStep === 1 && !uploaded) {
      formSubmitRef.current.handleSubmit();
    }
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1);
      setNextEnabled(false);
    } else {
      handleCloseDialog();
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
    if (
      newDataset.file !== null &&
      Object.keys(newDataset.params).length > 0 &&
      readyToUpload
    ) {
      handleSubmitNewDataset();
    }
  }, [newDataset]);

  useEffect(() => {
    if (requestError) {
      setActiveStep(1);
      setNextEnabled(false);
      setRequestError(false);
    }
  }, [requestError]);
  return (
    <Dialog
      open={open}
      onClose={handleCloseDialog}
      fullWidth
      maxWidth={"lg"}
      scroll="paper"
      PaperProps={{
        sx: { minHeight: "80vh" },
      }}
    >
      {/* Title */}
      <DialogTitle id="new-experiment-dialog-title">
        <Grid container direction={"row"} alignItems={"center"}>
          <Grid item xs={12} md={3}>
            <Typography
              variant="h6"
              component={"h3"}
              sx={{ mb: { sm: 2, md: 0 } }}
            >
              New dataset
            </Typography>
          </Grid>
          <Grid item xs={12} md={9}>
            <Stepper
              nonLinear
              activeStep={activeStep}
              sx={{ maxWidth: "100%" }}
            >
              {steps.map((step, index) => (
                <Step
                  key={`${step.name}`}
                  completed={activeStep > index}
                  disabled={activeStep < index}
                >
                  <StepButton color="inherit" onClick={handleStepButton(index)}>
                    {step.label}
                  </StepButton>
                </Step>
              ))}
            </Stepper>
          </Grid>
        </Grid>
      </DialogTitle>

      {/* Main content - steps */}
      <DialogContent dividers>
        {/* Step 1: select dataloader */}
        {activeStep === 0 && (
          <SelectDataloaderStep
            newDataset={newDataset}
            setNewDataset={setNewDataset}
            setNextEnabled={setNextEnabled}
          />
        )}
        {/* Step 2: Configure dataloader and upload file */}
        {activeStep === 1 && (
          <ConfigureAndUploadDataset
            newDataset={newDataset}
            setNewDataset={setNewDataset}
            setNextEnabled={setNextEnabled}
            formSubmitRef={formSubmitRef}
          />
        )}
        {/* Step 3: Dataset Summary and cast columns types */}
        {activeStep === 2 && (
          <DatasetSummaryStep
            uploadedDataset={uploadedDataset}
            setNextEnabled={setNextEnabled}
            datasetUploaded={uploaded}
          />
        )}
      </DialogContent>

      {/* Actions - Back and Next */}
      <DialogActions>
        <ButtonGroup size="large">
          <Button onClick={handleBackButton}>
            {activeStep === 0 ? "Close" : "Back"}
          </Button>
          <Button
            onClick={() => {
              if (activeStep === 1) {
                setReadyToUpload(true);
              }
              handleNextButton();
            }}
            autoFocus
            variant="contained"
            color="primary"
            disabled={!nextEnabled}
          >
            {activeStep === 2 ? "Save" : "Next"}
          </Button>
        </ButtonGroup>
      </DialogActions>
    </Dialog>
  );
}
DatasetModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  updateDatasets: PropTypes.func.isRequired,
};

export default DatasetModal;
