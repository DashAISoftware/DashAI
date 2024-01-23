import { DialogContent } from "@mui/material";
import PropTypes from "prop-types";
import React, { createContext, useContext, useState } from "react";
import StepperActions from "./StepperActions";
import StepperTitle from "./StepperTitle";

const StepperContext = createContext();

const StepperProvider = ({ children }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);

  const sharedData = {
    activeStep,
    setActiveStep,
    nextEnabled,
    setNextEnabled,
  };

  return (
    <StepperContext.Provider value={sharedData}>
      {children}
    </StepperContext.Provider>
  );
};

function StepperContainer({ children }) {
  return <StepperProvider>{children}</StepperProvider>;
}

function Title(props) {
  const { activeStep, setActiveStep } = useContext(StepperContext);
  return (
    <StepperTitle
      {...props}
      activeStep={activeStep}
      setActiveStep={setActiveStep}
    />
  );
}

function Body({ stepsComponents, stepsComponentsProps }) {
  const { activeStep, setNextEnabled } = useContext(StepperContext);

  const StepContent = stepsComponents[activeStep];

  return (
    <DialogContent dividers>
      <StepContent {...stepsComponentsProps} setNextEnabled={setNextEnabled} />
    </DialogContent>
  );
}

function Actions(props) {
  const { activeStep, setActiveStep, nextEnabled } = useContext(StepperContext);

  return (
    <StepperActions
      {...props}
      activeStep={activeStep}
      setActiveStep={setActiveStep}
      nextEnabled={nextEnabled}
    />
  );
}

StepperProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

StepperContainer.propTypes = {
  children: PropTypes.node.isRequired,
};

Body.propTypes = {
  stepsComponents: PropTypes.arrayOf(PropTypes.func.isRequired).isRequired,
  stepsComponentsProps: PropTypes.object.isRequired,
};

StepperContainer.Title = Title;
StepperContainer.Body = Body;
StepperContainer.Actions = Actions;

export default StepperContainer;
