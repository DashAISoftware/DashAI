import { Button, ButtonGroup, DialogActions } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

function StepperActions({
  onStartEdge,
  onEndEdge,
  activeStep,
  setActiveStep,
  nextEnabled,
}) {
  const isStartStep = activeStep === 0;
  const isEndStep = activeStep === 2;

  const handleBackButton = () => {
    isStartStep ? onStartEdge() : setActiveStep(activeStep - 1);
  };

  const handleNextButton = () => {
    isEndStep ? onEndEdge() : setActiveStep(activeStep + 1);
  };
  return (
    <DialogActions>
      <ButtonGroup size="large">
        <Button onClick={handleBackButton}>
          {isStartStep ? "Close" : "Back"}
        </Button>
        <Button
          onClick={handleNextButton}
          autoFocus
          variant="contained"
          color="primary"
          disabled={!nextEnabled}
        >
          {isEndStep ? "Save" : "Next"}
        </Button>
      </ButtonGroup>
    </DialogActions>
  );
}

StepperActions.propTypes = {
  onStartEdge: PropTypes.func.isRequired,
  onEndEdge: PropTypes.func.isRequired,
  activeStep: PropTypes.number.isRequired,
  setActiveStep: PropTypes.func.isRequired,
  nextEnabled: PropTypes.bool.isRequired,
};

export default StepperActions;
