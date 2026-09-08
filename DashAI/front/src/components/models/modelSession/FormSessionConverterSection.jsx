import { useState } from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import ScopeStepSessionConverter from "./ScopeStepSessionConverter";
import ParameterStepConverter from "../../notebooks/converterCreation/ParameterStepConverter";
import { updateSessionConverters } from "../../../api/modelSession";

/**
 * Session-flow counterpart to the notebook's FormConverterSection. Same
 * Scope -> Parameters stepper shape, but saving no longer executes or
 * polls anything: it just appends a new, unexecuted converter entry (as an
 * `input_scope` of atoms, see `buildAtomList`/`ScopeStepSessionConverter`)
 * to the session's converter list via `updateSessionConverters` (a PUT
 * that validates and replaces the full list, but never runs a job). The
 * real preprocessing job only runs once, when the wizard's Columns step
 * finalizes the whole session.
 */
export default function FormSessionConverterSection({
  step,
  setStep,
  handleClose,
  tool,
  atoms,
  session,
  onApplied,
  onApplyError,
}) {
  const { t } = useTranslation(["models"]);
  const { enqueueSnackbar } = useSnackbar();
  const [columns, setColumns] = useState([]);
  const [targetColumn, setTargetColumn] = useState(null);

  const hasParams = Object.values(tool.schema.properties).length > 0;

  const handleSaveConverter = async (params) => {
    const newEntry = {
      id: `conv_${(session.converters || []).length}_${Date.now()}`,
      converter: tool.name,
      params: params || {},
      input_scope: columns,
      target_column: targetColumn?.columnName ?? null,
    };
    handleClose();
    try {
      const updatedSession = await updateSessionConverters(session.id, [
        ...(session.converters || []),
        newEntry,
      ]);
      onApplied(updatedSession);
    } catch (error) {
      enqueueSnackbar(t("models:error.converterApplyFailed"), {
        variant: "error",
      });
      onApplyError(null);
    }
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
          atoms={atoms}
          columns={columns}
          setColumns={setColumns}
          targetColumn={targetColumn}
          setTargetColumn={setTargetColumn}
          session={session}
          nextStep={
            hasParams
              ? () => setStep((s) => s + 1)
              : () => handleSaveConverter({})
          }
        />
      )}
      {step === 1 && (
        <ParameterStepConverter
          converter={tool.name}
          tool={tool}
          selectedColumns={columns}
          initialParams={{}}
          handleSaveConverter={handleSaveConverter}
          setStep={setStep}
          saveButtonText={t("models:button.addConverter")}
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
  atoms: PropTypes.array.isRequired,
  session: PropTypes.object.isRequired,
  onApplied: PropTypes.func.isRequired,
  onApplyError: PropTypes.func.isRequired,
};
