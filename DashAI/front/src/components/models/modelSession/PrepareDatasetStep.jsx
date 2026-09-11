import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import {
  Grid,
  Box,
  Alert,
  AlertTitle,
  FormControlLabel,
  Switch,
  Typography,
} from "@mui/material";
import SplitDatasetRows from "./SplitDatasetRows";
import { useTranslation } from "react-i18next";
import { useModels } from "../ModelsContext";
import {
  buildSplitsPayload,
  resolveSplitterName,
  STRATEGY_KINDS,
  SPLIT_TYPES,
} from "../../../utils/splitsPayload";
/**
 * Step of the session wizard: configure the evaluation strategy, partitions,
 * and whether preprocessing converters should be applied before column
 * selection. Column selection itself lives in SelectColumnsStep.
 * @param {object} newExp object that contains the Session wizard state
 * @param {function} setNewExp updates the session wizard state (newExp)
 * @param {function} setNextEnabled function to enable or disable the "Next" button
 * @param {string} evaluationStrategy the evaluation strategy selected for the session
 * @param {function} setEvaluationStrategy function to update the evaluation strategy
 * @param {object} dataset the selected dataset
 * @param {object} datasetInfo dataset metadata fetched by the parent step
 * @param {boolean} infoLoading whether datasetInfo is still being fetched
 */
function PrepareDatasetStep({
  newExp,
  setNewExp,
  setNextEnabled,
  dataset,
  evaluationStrategy,
  setEvaluationStrategy,
  datasetInfo,
  infoLoading,
}) {
  const { setSessionRightContent } = useModels();
  const { t } = useTranslation(["experiments", "models", "common"]);

  const [applyPreprocessing, setApplyPreprocessing] = useState(
    Boolean(newExp.applyPreprocessing),
  );

  // Values submitted by the schema generated splitter form, and whether that
  // form currently reports a validation error.
  const [splitterParams, setSplitterParams] = useState(null);
  const [paramsError, setParamsError] = useState(false);

  // Cross-Validation configuration states
  const [cvType, setCvType] = useState(null);
  // Which holdout splitter this task uses. Resolved from the task rather
  // than hardcoded, so a time series cannot be handed a shuffling one.
  const [holdoutType, setHoldoutType] = useState(null);
  // The split shape of the selected strategy, reported by the backend. The
  // screens used to compare strategy names, which is why a new strategy
  // rendered nothing at all.
  const [strategyKind, setStrategyKind] = useState(null);
  const [groupColumn, setGroupColumn] = useState("");

  const defaultParitionsIndex = {
    train: [],
    validation: [],
    test: [],
  };
  const [datasetPartitionsIndex, setDatasetPartitionsIndex] = useState({});

  const [rowsPartitionsIndex, setRowsPartitionsIndex] = useState(
    defaultParitionsIndex,
  );
  const [splitType, setSplitType] = useState("");

  const [splitsReady, setSplitsReady] = useState(false);

  useEffect(() => {
    if (
      datasetInfo &&
      (datasetInfo.train_indices ||
        datasetInfo.val_indices ||
        datasetInfo.test_indices)
    ) {
      setDatasetPartitionsIndex({
        train: datasetInfo.train_indices || [],
        validation: datasetInfo.val_indices || [],
        test: datasetInfo.test_indices || [],
      });
    }
  }, [datasetInfo]);

  const updateExperiment = () => {
    const updatedExpData = {
      ...newExp,
      evaluation_strategy: evaluationStrategy,
      applyPreprocessing: applyPreprocessing,
    };

    const splitterName = resolveSplitterName(strategyKind, cvType, holdoutType);
    if (splitterName) {
      updatedExpData.splits = buildSplitsPayload({
        splitterName,
        splitType:
          strategyKind === STRATEGY_KINDS.HOLDOUT ? splitType : SPLIT_TYPES.CV,
        params: {
          ...(splitterParams ?? {}),
          // The group column select is rendered by hand, so its value is not
          // part of the generated form's values.
          ...(cvType?.schema?.properties?.group_column
            ? { group_column: groupColumn }
            : {}),
        },
        indexes:
          splitType === SPLIT_TYPES.PREDEFINED
            ? datasetPartitionsIndex
            : rowsPartitionsIndex,
      });
    }

    setNewExp(updatedExpData);
  };

  useEffect(() => {
    if (splitsReady) {
      updateExperiment();
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [
    splitsReady,
    splitType,
    splitterParams,
    cvType,
    holdoutType,
    strategyKind,
    groupColumn,
    evaluationStrategy,
    applyPreprocessing,
    rowsPartitionsIndex,
    datasetPartitionsIndex,
  ]);

  // Push SplitDatasetRows (or loading spinner) into the right bar
  useEffect(() => {
    if (infoLoading) {
      setSessionRightContent(null);
      return () => setSessionRightContent(null);
    }
    setSessionRightContent(
      <SplitDatasetRows
        datasetInfo={datasetInfo}
        rowsPartitionsIndex={rowsPartitionsIndex}
        setRowsPartitionsIndex={setRowsPartitionsIndex}
        setSplitsReady={setSplitsReady}
        splitType={splitType}
        setSplitType={setSplitType}
        SPLIT_TYPES={SPLIT_TYPES}
        splitterParams={splitterParams}
        setSplitterParams={setSplitterParams}
        paramsError={paramsError}
        setParamsError={setParamsError}
        evaluationStrategy={evaluationStrategy}
        setEvaluationStrategy={setEvaluationStrategy}
        cvType={cvType}
        setCvType={setCvType}
        holdoutType={holdoutType}
        setHoldoutType={setHoldoutType}
        strategyKind={strategyKind}
        setStrategyKind={setStrategyKind}
        groupColumn={groupColumn}
        setGroupColumn={setGroupColumn}
        inputColumnNames={datasetInfo.column_names || []}
        taskName={newExp.task_name}
      />,
    );
    return () => setSessionRightContent(null);
  }, [
    infoLoading,
    datasetInfo,
    rowsPartitionsIndex,
    splitType,
    splitterParams,
    paramsError,
    evaluationStrategy,
    cvType,
    holdoutType,
    strategyKind,
    groupColumn,
  ]);

  return (
    <React.Fragment>
      {!infoLoading && datasetInfo.nan ? (
        Object.values(datasetInfo.nan).some((v) => v > 0) ? (
          <Alert
            severity="warning"
            sx={{
              mb: 2,
              "& .MuiAlert-icon": { fontSize: 24 },
              bgcolor: (theme) => `${theme.palette.warning.main}40`,
              border: (theme) => `1px solid ${theme.palette.warning.main}`,
            }}
          >
            <AlertTitle>
              {t("experiments:label.missingValuesDetected")}
            </AlertTitle>
            <Grid container spacing={4}>
              {Object.entries(datasetInfo.nan)
                .filter(([_, count]) => count > 0)
                .map(([col, count]) => (
                  <Grid size={{ xs: 12 }} key={col}>
                    - {col}: {count} {t("experiments:label.missingValues")}
                  </Grid>
                ))}
            </Grid>
            <p>{t("experiments:label.recommendPreprocessMissingValues")}</p>
          </Alert>
        ) : null
      ) : null}

      <Box
        sx={{
          mt: 2,
          p: 6,
          border: 1,
          borderColor: "divider",
          borderRadius: 2,
        }}
      >
        <FormControlLabel
          control={
            <Switch
              checked={applyPreprocessing}
              onChange={(event) => setApplyPreprocessing(event.target.checked)}
            />
          }
          label={t("models:label.applyPreprocessing")}
        />
        <Typography variant="caption" component="p" sx={{ color: "grey" }}>
          {t("models:label.applyPreprocessingDescription")}
        </Typography>
      </Box>
    </React.Fragment>
  );
}

PrepareDatasetStep.propTypes = {
  newExp: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    dataset: PropTypes.object,
    task_name: PropTypes.string,
    input_columns: PropTypes.arrayOf(PropTypes.string),
    output_columns: PropTypes.arrayOf(PropTypes.string),
    splits: PropTypes.object,
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
    applyPreprocessing: PropTypes.bool,
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  dataset: PropTypes.object.isRequired,
  evaluationStrategy: PropTypes.string,
  setEvaluationStrategy: PropTypes.func,
  datasetInfo: PropTypes.object,
  infoLoading: PropTypes.bool,
};
export default PrepareDatasetStep;
