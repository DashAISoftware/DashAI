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
  Grid,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";

import SetNameAndTaskStep from "./SetNameAndTaskStep";
// import SetExperimentName from "./SetExperimentNameStep";
import SelectDatasetStep from "./SelectDatasetStep";

const steps = [
  { name: "selectTask", label: "Set name and task" },
  { name: "selectDataset", label: "Select dataset" },
  { name: "configureModels", label: "Configure models" },
];

const defaultNewExp = {
  id: "",
  name: "",
  dataset: null,
  task_name: "",
  step: "SET_NAME",
  created: null,
  last_modified: null,
  runs: [],
};

export default function NewExperimentModal({ open, setOpen }) {
  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.down("md"));

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
      <DialogTitle id="new-experiment-dialog-title">
        <Grid container direction={"row"} alignItems={"center"}>
          <Grid item xs={12} md={3}>
            <Typography
              variant="h6"
              component={"h3"}
              align={matches ? "center" : "left"}
              sx={{ mb: { sm: 2, md: 0 } }}
            >
              New experiment
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
          <SetNameAndTaskStep
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
          />
        )}
        {activeStep === 1 && (
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
