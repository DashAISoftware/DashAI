import React, { useState } from "react";
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
import ItemsList from "./ItemsList";

const steps = [
  { name: "selectTask", label: "select Task" },
  { name: "selectDataloader", label: "Select how to load" },
  { name: "uploadDataset", label: "Configure and upload your dataset" },
];

const defaultNewDataset = {
  task_name: "",
  dataloader_name: "",
};

/**
 * This component renders a modal that takes the user through the process of uploading a new dataset.
 * @param {bool} open true to open the modal, false to close it
 * @param {function} setOpen function to modify the value of open
 */
function NewDatasetModal({ open, setOpen }) {
  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);
  const [newDataset, setNewDataset] = useState(defaultNewDataset);

  const handleCloseDialog = () => {
    setActiveStep(0);
    setOpen(false);
    setNewDataset(defaultNewDataset);
    setNextEnabled(false);
  };

  const handleStepButton = (stepIndex) => () => {
    setActiveStep(stepIndex);
  };

  const handleNextButton = () => {
    if (activeStep < steps.length) {
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

  return (
    <Dialog
      open={open}
      onClose={() => setOpen(false)}
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
        {activeStep === 0 && (
          <ItemsList
            itemsType="tasks"
            itemsName="task"
            newDataset={newDataset}
            setNewDataset={setNewDataset}
            setNextEnabled={setNextEnabled}
          />
        )}
        {activeStep === 1 && (
          <ItemsList
            itemsType="dataloaders"
            itemsName="way to upload your data"
            newDataset={newDataset}
            setNewDataset={setNewDataset}
            setNextEnabled={setNextEnabled}
          />
        )}
        {/* TODO: step 3 configuration and upload file */}
        {activeStep === 2 && <div />}
      </DialogContent>

      {/* Actions - Back and Next */}
      <DialogActions>
        <ButtonGroup size="large">
          <Button onClick={handleBackButton}>
            {activeStep === 0 ? "Close" : "Back"}
          </Button>
          <Button
            onClick={handleNextButton}
            autoFocus
            variant="contained"
            color="primary"
            disabled={!nextEnabled}
          >
            Next
          </Button>
        </ButtonGroup>
      </DialogActions>
    </Dialog>
  );
}
NewDatasetModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
};

export default NewDatasetModal;
