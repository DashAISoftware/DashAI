import React, { useMemo } from "react";
import { useStrategyKind } from "../../hooks/useStrategyKind";
import { STRATEGY_KINDS } from "../../utils/splitsPayload";
import PropTypes from "prop-types";
import { Box, Typography, TextField } from "@mui/material";
import { useTranslation } from "react-i18next";
import FormSchemaWithSelectedModel from "../shared/FormSchemaWithSelectedModel";
import FormSchemaContainer from "../shared/FormSchemaContainer";
import OptimizationTableSelectOptimizer from "./modelSession/OptimizationTableSelectOptimizer";
import ModelsTableSelectMetric from "./modelSession/ModelsTableSelectMetric";
import NestedCVSelector from "./modelSession/NestedCVSelector";
import { useModels } from "./ModelsContext";

/**
 * The actual "edit a run's parameters" form body, split into the same two
 * steps as AddModelDialog: step 0 is the run name and model parameters,
 * step 1 (only reachable when a parameter is marked for optimization) is
 * the goal metric, optimizer, and its parameters. Rendered inside the
 * "Edit Run" dialog (RunEditDialog), which owns the step/Stepper and the
 * Back/Next/Save actions.
 */
export default function RunEditForm({
  run,
  activeStep,
  taskName,
  editedName,
  setEditedName,
  editedParameters,
  handleParametersChange,
  editedOptimizer,
  editedOptimizerParams,
  setEditedOptimizerParams,
  handleOptimizerParamsChange,
  handleOptimizerSelected,
  editedGoalMetric,
  setEditedGoalMetric,
  editedUseNestedCV,
  setEditedUseNestedCV,
  editedInnerConfig,
  setEditedInnerConfig,
}) {
  const { t } = useTranslation(["models", "common"]);
  const { selectedSession: session, datasetRowCount } = useModels();

  // Nested cross-validation only applies to a folded strategy, which the
  // backend reports rather than the strategy name implying it.
  const isCrossValidation =
    useStrategyKind(session?.evaluation_strategy) === STRATEGY_KINDS.CV;

  const outerSplit = useMemo(() => {
    return session?.splits ? JSON.parse(session.splits) : null;
  }, [session?.splits]);

  // The outer folds are built over the rows left after the carve, so an
  // inner fold cannot draw from the reserved ones.
  const maxInnerFolds = Math.floor(
    (datasetRowCount * (1 - (Number(outerSplit?.test_size) || 0))) /
      outerSplit?.n_splits,
  );

  if (activeStep === 1) {
    return (
      <Box sx={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <Typography variant="subtitle2">
          {t("models:label.optimizerConfiguration")}
        </Typography>

        <Box>
          <Typography variant="body2" sx={{ mb: 2 }}>
            {t("models:label.goalMetric")} *
          </Typography>
          <ModelsTableSelectMetric
            taskName={taskName}
            metricName={editedGoalMetric}
            handleSelectedMetric={setEditedGoalMetric}
            required
            autoSelectDefault
          />
        </Box>

        <Box>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {t("models:label.optimizer")} *
          </Typography>
          <OptimizationTableSelectOptimizer
            taskName={taskName}
            optimizerName={editedOptimizer}
            handleSelectedOptimizer={handleOptimizerSelected}
          />
        </Box>

        {isCrossValidation && (
          <NestedCVSelector
            useNestedCV={editedUseNestedCV}
            onChange={setEditedUseNestedCV}
            innerConfig={editedInnerConfig}
            onInnerConfigChange={setEditedInnerConfig}
            outerSplit={outerSplit}
            maxInnerFolds={maxInnerFolds}
          />
        )}

        {editedOptimizer && (
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 4 }}>
              {t("common:optimizerParameters")}
            </Typography>
            <FormSchemaContainer key={editedOptimizer}>
              <FormSchemaWithSelectedModel
                modelToConfigure={editedOptimizer}
                initialValues={editedOptimizerParams}
                onFormSubmit={(values) => setEditedOptimizerParams(values)}
                onValuesChange={handleOptimizerParamsChange}
                onCancel={() => {}}
                hideButtons
              />
            </FormSchemaContainer>
          </Box>
        )}
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <TextField
        label={t("models:label.runName")}
        value={editedName}
        onChange={(e) => setEditedName(e.target.value)}
        fullWidth
        required
        size="small"
      />

      {run.model_name && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 2 }}>
            {t("common:modelParameters")}
          </Typography>
          <FormSchemaContainer>
            <FormSchemaWithSelectedModel
              modelToConfigure={run.model_name}
              initialValues={editedParameters}
              onFormSubmit={handleParametersChange}
              onValuesChange={handleParametersChange}
              onCancel={() => {}}
              hideButtons
            />
          </FormSchemaContainer>
        </Box>
      )}
    </Box>
  );
}

RunEditForm.propTypes = {
  run: PropTypes.shape({
    model_name: PropTypes.string,
  }).isRequired,
  activeStep: PropTypes.number.isRequired,
  taskName: PropTypes.string,
  editedName: PropTypes.string.isRequired,
  setEditedName: PropTypes.func.isRequired,
  editedParameters: PropTypes.object.isRequired,
  handleParametersChange: PropTypes.func.isRequired,
  editedOptimizer: PropTypes.string.isRequired,
  editedOptimizerParams: PropTypes.object.isRequired,
  setEditedOptimizerParams: PropTypes.func.isRequired,
  handleOptimizerParamsChange: PropTypes.func.isRequired,
  handleOptimizerSelected: PropTypes.func.isRequired,
  editedGoalMetric: PropTypes.string.isRequired,
  setEditedGoalMetric: PropTypes.func.isRequired,
};
