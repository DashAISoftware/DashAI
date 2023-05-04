import React, { useState } from "react";
import PropTypes from "prop-types";

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  ButtonGroup,
  Stepper,
  Step,
  StepButton,
} from "@mui/material";

import SelectTaskStep from "./SelectTaskStep";
import SetExperimentName from "./SetExperimentNameStep";
import SelectDatasetStep from "./SelectDatasetStep";

const steps = [
  {
    name: "setExperimentName",
    label: "Set name",
  },
  { name: "selectTask", label: "Select task" },
  { name: "selectDataset", label: "Select dataset" },
  { name: "configureModels", label: "Configure models" },
];

const defaultNewExp = {
  id: null,
  name: null,
  dataset: null,
  task_name: null,
  step: "SET_NAME",
  created: null,
  last_modified: null,
  runs: [],
};

export default function NewExperimentModal({ open, setOpen }) {
  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);
  const [newExp, setNewExp] = useState(defaultNewExp);

  const handleCloseDialog = () => {
    setActiveStep(0);
    setOpen(false);
    setNewExp(defaultNewExp);
    setNextEnabled(false);
  };

  const handleStepButton = (stepIndex) => () => {
    setActiveStep(stepIndex);
  };

  const handleBackButton = () => {
    if (activeStep === 0) {
      handleCloseDialog();
    } else {
      setActiveStep(activeStep - 1);
    }
  };

  const handleNextButton = () => {
    console.log(newExp);
    if (activeStep < steps.length) {
      setActiveStep(activeStep + 1);
      setNextEnabled(false);
    } else {
      handleCloseDialog();
    }
  };

  return (
    <Dialog
      open={open}
      fullWidth
      maxWidth={"lg"}
      onClose={handleCloseDialog}
      aria-labelledby="new-experiment-dialog-title"
      aria-describedby="new-experiment-dialog-description"
      scroll="paper"
      PaperProps={{
        sx: { minHeight: "80vh" },
      }}
    >
      {/* Title */}
      <DialogTitle id="new-experiment-dialog-title">New experiment</DialogTitle>

      {/* Stepper */}

      {/* Main content - steps */}
      <DialogContent dividers>
        <Stepper
          nonLinear
          activeStep={activeStep}
          sx={{ maxWidth: "100%", mt: 2, mb: 3 }}
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
        {activeStep === 0 && (
          <SetExperimentName
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
          />
        )}
        {activeStep === 1 && (
          <SelectTaskStep
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
          />
        )}
        {activeStep === 2 && (
          <SelectDatasetStep
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
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

NewExperimentModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
};
