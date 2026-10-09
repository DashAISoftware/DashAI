import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";
import ScopeStepSessionConverter from "./ScopeStepSessionConverter";
import ParameterStepConverter from "../../notebooks/converterCreation/ParameterStepConverter";

/**
 * "Add a converter" form for the session wizard's preprocessing step,
 * mirroring the notebook's FormConverterSection (same two-step scope/params
 * flow, same ParameterStepConverter for the second step). A session
 * converter is never fit immediately: saving here only appends
 * `{converter, params, scope}` to the session's local `preprocessing` list.
 * What the step produces is estimated by the backend afterwards (see
 * usePreprocessingStructure), and the actual fit happens once, when the
 * session is created (see the backend's PreprocessingJob).
 */
export default function FormSessionConverterSection({
  step,
  setStep,
  handleClose,
  tool,
  newExp,
  setNewExp,
  finalState,
  stepDisplayNames,
  filePath,
  hideButtons = false,
}) {
  const [scope, setScope] = useState([]);

  const handleSaveConverter = async (params) => {
    const newStep = {
      converter: tool.name,
      params: params || {},
      scope,
    };
    setNewExp({
      ...newExp,
      preprocessing: [...(newExp.preprocessing || []), newStep],
    });
    handleClose();
  };

  return (
    <Box
      sx={{
        overflow: "visible",
        display: "flex",
        flexDirection: "column",
        flex: 1,
        maxHeight: "100%",
        minHeight: 0,
      }}
    >
      {step === 0 && (
        <ScopeStepSessionConverter
          tool={tool}
          finalState={finalState}
          stepDisplayNames={stepDisplayNames}
          filePath={filePath}
          scope={scope}
          setScope={setScope}
          nextStep={
            Object.values(tool.schema.properties).length > 0
              ? () => setStep((s) => s + 1)
              : () => handleSaveConverter({})
          }
        />
      )}

      {step === 1 && (
        <ParameterStepConverter
          converter={tool.name}
          tool={tool}
          selectedColumns={scope}
          initialParams={{}}
          handleSaveConverter={handleSaveConverter}
          setStep={setStep}
          hideButtons={hideButtons}
          warnAboutLeakage={false}
        />
      )}
    </Box>
  );
}

FormSessionConverterSection.propTypes = {
  step: PropTypes.number.isRequired,
  setStep: PropTypes.func.isRequired,
  handleClose: PropTypes.func.isRequired,
  tool: PropTypes.object.isRequired,
  newExp: PropTypes.object.isRequired,
  setNewExp: PropTypes.func.isRequired,
  // The estimated dataset state at the end of the chain, where the new
  // converter will be appended.
  finalState: PropTypes.array.isRequired,
  stepDisplayNames: PropTypes.arrayOf(PropTypes.string).isRequired,
  filePath: PropTypes.string,
  hideButtons: PropTypes.bool,
};
