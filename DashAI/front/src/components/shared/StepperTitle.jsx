import CloseIcon from "@mui/icons-material/Close";
import {
  Box,
  DialogTitle,
  IconButton,
  Step,
  StepButton,
  Stepper,
  Typography,
} from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

function StepperTitle({
  title,
  handleClose,
  steps,
  activeStep,
  setActiveStep,
}) {
  return (
    <DialogTitle id="new-experiment-dialog-title">
      <Box display="flex" alignItems="flex" justifyContent="flex-end">
        <Box flex={1}>
          <IconButton
            edge="start"
            color="inherit"
            onClick={handleClose}
            sx={{ display: { xs: "flex", sm: "none" } }}
          >
            <CloseIcon />
          </IconButton>

          <Typography variant="h6" component="h3" sx={{ mb: { sm: 2, md: 0 } }}>
            {title}
          </Typography>
        </Box>
        <Box flex={2}>
          <Stepper nonLinear activeStep={activeStep} sx={{ maxWidth: "100%" }}>
            {steps.map((step, index) => (
              <Step
                expanded
                key={`${step.name}`}
                completed={activeStep > index}
                disabled={activeStep < index}
              >
                <StepButton
                  color="inherit"
                  onClick={() => setActiveStep(index)}
                >
                  {step.label}
                </StepButton>
              </Step>
            ))}
          </Stepper>
        </Box>
      </Box>
    </DialogTitle>
  );
}

StepperTitle.propTypes = {
  handleClose: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  steps: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
    }),
  ),
  activeStep: PropTypes.number.isRequired,
  setActiveStep: PropTypes.func.isRequired,
};

export default StepperTitle;
