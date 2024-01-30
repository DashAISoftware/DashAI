import PropTypes from "prop-types";
import React, { useState } from "react";
import StepperContainer from "../../../components/shared/StepperContainer";
import StepperDialog from "../../../components/shared/StepperDialog";
import { defaultNewExp } from "../constants/experiments";
import useExperimentsCreate from "../hooks/useExperimentsCreate";
import ExperimentsCreateDatasetStep from "./ExperimentsCreateDatasetStep";
import ExperimentsCreateModelsStep from "./ExperimentsCreateModelsStep";
import ExperimentsCreateTaskStep from "./ExperimentsCreateTaskStep";
const steps = [
  { name: "selectTask", label: "Set name and task" },
  { name: "selectDataset", label: "Select dataset" },
  { name: "configureModels", label: "Configure models" },
];

const stepsComponents = [
  ExperimentsCreateTaskStep,
  ExperimentsCreateDatasetStep,
  ExperimentsCreateModelsStep,
];

function ExperimentsCreateDialog({
  open,
  handleCloseDialog,
  updateExperiments,
}) {
  const [newExp, setNewExp] = useState(defaultNewExp);

  const { uploadNewExperiment } = useExperimentsCreate({
    newExp,
    onSuccess: () => updateExperiments(),
  });

  const onClose = () => {
    setNewExp(defaultNewExp);
    handleCloseDialog();
  };

  return (
    <StepperDialog open={open} onClose={onClose}>
      <StepperContainer>
        <StepperContainer.Title
          handleClose={onClose}
          title={"New experiment"}
          steps={steps}
        />
        <StepperContainer.Body
          stepsComponents={stepsComponents}
          stepsComponentsProps={{ newExp, setNewExp }}
        />
        <StepperContainer.Actions
          onStartEdge={() => onClose()}
          onEndEdge={() => {
            uploadNewExperiment();
            onClose();
          }}
        />
      </StepperContainer>
    </StepperDialog>
  );
}

export default ExperimentsCreateDialog;

ExperimentsCreateDialog.propTypes = {
  handleCloseDialog: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired,
  updateExperiments: PropTypes.func.isRequired,
};
