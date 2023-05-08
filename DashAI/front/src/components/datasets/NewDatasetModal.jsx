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
import SchemaList from "../SchemaList";

const steps = [
  { name: "selectTask", label: "select Task" },
  { name: "selectDataloader", label: "Select how to load" },
  { name: "configureDataset", label: "Configure your dataset" },
  { name: "uploadDataset", label: "Upload your dataset" },
];

const defaultNewDataset = {
  task_name: "",
};

function NewDatasetModal({ open, setOpen }) {
  const [activeStep, setActiveStep] = useState(0);
  // const [nextEnabled, setNextEnabled] = useState(false);
  const [newDataset, setNewDataset] = useState(defaultNewDataset);

  const handleCloseDialog = () => {
    setActiveStep(0);
    setOpen(false);
  };

  const handleNextButton = () => {
    if (activeStep < steps.length) {
      setActiveStep(activeStep + 1);
      // setNextEnabled(false);
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
      <DialogTitle id="new-experiment-dialog-title">
        <Grid container direction={"row"} alignItems={"center"}>
          <Grid item xs={12} md={3}>
            <Typography
              variant="h6"
              component={"h3"}
              // align={matches ? "center" : "left"}
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
                  <StepButton color="inherit" onClick={() => {}}>
                    {step.label}
                  </StepButton>
                </Step>
              ))}
            </Stepper>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent dividers>
        {activeStep === 0 && (
          <SchemaList
            schemaName="tasks"
            itemsName="task"
            newDataset={newDataset}
            setNewDataset={setNewDataset}
          />
        )}
        {activeStep === 1 && (
          <SchemaList
            schemaName="TabularClassificationTask"
            itemsName="Way to upload your data"
            newDataset={newDataset}
            setNewDataset={setNewDataset}
          />
        )}
      </DialogContent>
      <DialogActions>
        <ButtonGroup size="large">
          <Button onClick={handleBackButton}>Back</Button>
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
NewDatasetModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
};

export default NewDatasetModal;
