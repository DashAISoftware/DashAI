import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";
import ScopeStepSessionConverter from "./ScopeStepSessionConverter";
import ParameterStepConverter from "../../notebooks/converterCreation/ParameterStepConverter";
import { resolveDeclaredOutputSlots } from "./sessionColumnRefs";

/**
 * "Add a converter" form for the session wizard's preprocessing step —
 * mirrors the notebook's FormConverterSection (same two-step scope/params
 * flow, same ParameterStepConverter for the second step), but a session
 * converter is never fit immediately: saving here only appends
 * `{converter, params, scope}` to the session's local `preprocessing` list.
 * The actual fit happens once, later, when the session is created (see the
 * backend's PreprocessingJob) — never from this form.
 */
export default function FormSessionConverterSection({
  step,
  setStep,
  handleClose,
  tool,
  newExp,
  setNewExp,
  datasetTypes,
  filePath,
  hideButtons = false,
}) {
  const [scope, setScope] = useState([]);

  const handleSaveConverter = async (params) => {
    const outputSlots = resolveDeclaredOutputSlots({
      tool,
      params,
      scope,
      datasetTypes,
      preprocessing: newExp.preprocessing,
    });
    const newStep = {
      converter: tool.name,
      params: params || {},
      scope,
      outputSlots,
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
          datasetTypes={datasetTypes}
          preprocessing={newExp.preprocessing}
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
  datasetTypes: PropTypes.object.isRequired,
  filePath: PropTypes.string,
  hideButtons: PropTypes.bool,
};
