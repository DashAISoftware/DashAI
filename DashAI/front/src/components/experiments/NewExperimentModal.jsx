import * as React from "react";
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

const steps = [
  {
    name: "setExperimentName",
    label: "Set name",
  },
  { name: "selectTask", label: "Select task" },
  { name: "selectDataset", label: "Select dataset" },
  { name: "configureModels", label: "Configure models" },
];

export default function NewExperimentModal({ open, setOpen }) {
  const [activeStep, setActiveStep] = React.useState(0);

  const handleCloseDialog = () => {
    setActiveStep(0);
    setOpen(false);
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
    if (activeStep < steps.length) {
      setActiveStep(activeStep + 1);
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
      <DialogContent dividers sx={{ py: 4 }}>
        <Stepper
          nonLinear
          activeStep={activeStep}
          sx={{ maxWidth: "100%", mt: 0, mb: 3 }}
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
        {activeStep === 0 && <SetExperimentName />}
        {activeStep === 1 && <SelectTaskStep />}
        {activeStep === 2 && <div>TODO...</div>}
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
