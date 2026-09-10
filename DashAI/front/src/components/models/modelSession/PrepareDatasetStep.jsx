import React, { useEffect, useLayoutEffect, useState } from "react";
import PropTypes from "prop-types";

import {
  Grid,
  CircularProgress,
  Box,
  Alert,
  AlertTitle,
  Chip,
} from "@mui/material";
import DivideDatasetColumns from "./DivideDatasetColumns";
import SplitDatasetRows from "./SplitDatasetRows";
import {
  getDatasetInfo as getDatasetInfoRequest,
  getDatasetTypes as getDatasetTypesRequest,
} from "../../../api/datasets";
import { getComponents as getComponentsRequest } from "../../../api/component";
import { validateColumns as validateColumnsRequest } from "../../../api/modelSession";
import { useSnackbar } from "notistack";
import { getColorByColumnType } from "../../../utils";
import { useTranslation } from "react-i18next";
import { Trans } from "react-i18next";
import { useModels } from "../ModelsContext";
import {
  buildSplitsPayload,
  resolveSplitterName,
  STRATEGY_KINDS,
  SPLIT_TYPES,
} from "../../../utils/splitsPayload";
/**
 * Step of the experiment modal: Set the input and output columns to use for clasification
 * and the splits for training, validation and testing.
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the modal
 * @param {string} evaluationStrategy the evaluation strategy selected for the experiment, either holdout or cross-validation
 * @param {function} setEvaluationStrategy function to update the evaluation strategy in the parent component (CreateSessionSteps)
 */
function PrepareDatasetStep({
  newExp,
  setNewExp,
  setNextEnabled,
  dataset,
  evaluationStrategy,
  setEvaluationStrategy,
}) {
  const { setSessionRightContent } = useModels();
  const [datasetInfo, setDatasetInfo] = useState({});
  const [datasetTypes, setDatasetTypes] = useState({});
  const { enqueueSnackbar } = useSnackbar();
  const [infoLoading, setInfoLoading] = useState(true);
  const { t } = useTranslation(["experiments", "common"]);

  // null means "not fetched yet" — distinct from the empty-but-loaded shape
  // getTaskRequirements falls back to when the task genuinely isn't found.
  // The banner below only renders once this is non-null, otherwise it briefly
  // interpolates its message with blank task name/types/cardinality.
  const [taskRequirements, setTaskRequirements] = useState(null);

  const [inputColumnNames, setInputColumnNames] = useState(
    newExp.input_columns,
  );
  const [outputColumnNames, setOutputColumnNames] = useState(
    newExp.output_columns,
  );

  const columnsReady =
    inputColumnNames.length >= 1 && outputColumnNames.length >= 1;
  const [columnsAreValid, setColumnsAreValid] = useState(false);
  // True until the current column selection has actually been checked against
  // the backend at least once — distinct from columnsAreValid=false, so the
  // banner doesn't flash red while columns are still being auto-selected or a
  // check is in flight, only once a real valid/invalid result is known.
  const [validationPending, setValidationPending] = useState(true);

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

  const getDatasetInfo = async () => {
    if (!dataset?.id) return;
    setInfoLoading(true);
    setInputColumnNames([]);
    setOutputColumnNames([]);
    try {
      const [fetchedDatasetInfo, fetchedDatasetTypes] = await Promise.all([
        getDatasetInfoRequest(dataset.id),
        getDatasetTypesRequest(dataset.id),
      ]);
      setDatasetInfo(fetchedDatasetInfo);
      setDatasetTypes(fetchedDatasetTypes);

      if (fetchedDatasetInfo) {
        setDatasetPartitionsIndex({
          train: fetchedDatasetInfo.train_indices || [],
          validation: fetchedDatasetInfo.val_indices || [],
          test: fetchedDatasetInfo.test_indices || [],
        });
      }

      if (
        fetchedDatasetInfo &&
        fetchedDatasetInfo.column_names &&
        fetchedDatasetInfo.column_names.length > 0
      ) {
        const allNames = fetchedDatasetInfo.column_names;
        if (
          inputColumnNames.length === 0 &&
          (!newExp.input_columns || newExp.input_columns.length === 0)
        ) {
          if (allNames.length > 1) {
            setInputColumnNames(allNames.slice(0, -1));
          } else if (allNames.length === 1) {
            setInputColumnNames([allNames[0]]);
          }
        }

        if (
          outputColumnNames.length === 0 &&
          (!newExp.output_columns || newExp.output_columns.length === 0)
        ) {
          if (allNames.length > 0) {
            setOutputColumnNames([allNames[allNames.length - 1]]);
          }
        }
      }
    } catch (error) {
      enqueueSnackbar(t("experiments:error.errorFetchingDatasetInfo"));
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setInfoLoading(false);
    }
  };

  const getTaskRequirements = async () => {
    try {
      const taskComponents = await getComponentsRequest({
        selectTypes: ["Task"],
      });

      const currentTask = taskComponents.find(
        (task) => task.name === newExp.task_name,
      );
      if (currentTask) {
        setTaskRequirements(currentTask);
      } else {
        enqueueSnackbar(
          t("experiments:error.taskRequirementsNotFound", {
            taskName: newExp.task_name,
          }),
        );
        setTaskRequirements({
          name: newExp.task_name,
          metadata: {
            inputs_types: [],
            inputs_cardinality: "",
            outputs_types: [],
            outputs_cardinality: "",
          },
        });
      }
    } catch (error) {
      enqueueSnackbar(t("experiments:error.errorFetchingTaskRequirements"));
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const validateColumns = async () => {
    try {
      if (
        !datasetInfo ||
        !datasetInfo.column_names ||
        datasetInfo.column_names.length === 0
      ) {
        setColumnsAreValid(false);
        return;
      }

      if (inputColumnNames.length === 0 || outputColumnNames.length === 0) {
        setColumnsAreValid(false);
        return;
      }

      const validation = await validateColumnsRequest(
        newExp.task_name,
        dataset.id,
        inputColumnNames,
        outputColumnNames,
      );
      setColumnsAreValid(validation.dataset_status === "valid");
    } catch (error) {
      enqueueSnackbar(t("experiments:error.errorFetchingColumnsValidation"));
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
      setColumnsAreValid(false);
    } finally {
      setValidationPending(false);
    }
  };

  const updateExperiment = () => {
    if (
      !datasetInfo ||
      !datasetInfo.column_names ||
      datasetInfo.column_names.length === 0
    ) {
      return;
    }

    const updatedExpData = {
      ...newExp,
      input_columns: inputColumnNames,
      output_columns: outputColumnNames,
      evaluation_strategy: evaluationStrategy,
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

  // Column validity depends on the columns, the dataset and the task, never on
  // the split configuration. Gating it on the splits being ready made every
  // split change re-check the columns over HTTP and blank the requirements
  // banner in the meantime.
  //
  // When columnsReady is false we already know the selection is invalid
  // (input or output is empty) without asking the backend, so
  // validationPending goes straight to false — otherwise the requirements
  // banner below stayed hidden forever after the user cleared a column,
  // instead of showing why the selection is invalid.
  //
  // This runs as a layout effect (not a regular effect) so that when
  // columns go from empty back to a ready selection — e.g. the dataset
  // finishes loading and auto-selects defaults — validationPending flips
  // back to true synchronously before the browser paints. A regular effect
  // runs one commit too late: React would paint a frame with the stale
  // "already validated" state (an incorrect red banner) against the new,
  // not-yet-checked columns before the effect corrected it.
  useLayoutEffect(() => {
    if (!columnsReady) {
      setColumnsAreValid(false);
      setValidationPending(false);
      return;
    }
    if (
      datasetInfo &&
      datasetInfo.column_names &&
      datasetInfo.column_names.length > 0
    ) {
      setValidationPending(true);
      validateColumns();
    }
  }, [columnsReady, inputColumnNames, outputColumnNames, datasetInfo]);

  useEffect(() => {
    if (columnsAreValid && splitsReady && columnsReady) {
      updateExperiment();
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [
    columnsReady,
    splitsReady,
    columnsAreValid,
    splitType,
    splitterParams,
    inputColumnNames,
    outputColumnNames,
    cvType,
    holdoutType,
    strategyKind,
    groupColumn,
    evaluationStrategy,
    rowsPartitionsIndex,
    datasetPartitionsIndex,
  ]);

  useEffect(() => {
    getDatasetInfo();
  }, [dataset?.id]);

  useEffect(() => {
    getTaskRequirements();
  }, []);

  // Push SplitDatasetRows (or loading spinner) into the right bar
  useEffect(() => {
    if (infoLoading) {
      setSessionRightContent(
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            height: "100%",
          }}
        >
          <CircularProgress size={32} />
        </Box>,
      );
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
        inputColumnNames={inputColumnNames}
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
    inputColumnNames,
  ]);

  const columnGroupsOf = (side) => {
    const metadata = taskRequirements?.metadata ?? {};
    if (Array.isArray(metadata[side]) && metadata[side].length > 0) {
      return metadata[side];
    }
    const cardinality = metadata[`${side}_cardinality`];
    return [
      {
        types: metadata[`${side}_types`] ?? [],
        min: cardinality === "n" ? 0 : cardinality,
        max: cardinality,
      },
    ];
  };

  const describeCardinality = ({ min, max }) => {
    if (max === "n") {
      return min ? t("experiments:label.cardinalityAtLeast", { min }) : "n";
    }
    if (min === max) {
      return String(max);
    }
    return t("experiments:label.cardinalityBetween", { min, max });
  };

  const renderTypesAsChips = (typesList) => {
    if (!typesList || typesList.length === 0) {
      return <span>{t("common:any")}</span>;
    }

    return (
      <Box
        component="span"
        sx={{
          display: "inline-flex",
          gap: 1,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        {typesList.map((type, index) => (
          <React.Fragment key={type}>
            <Chip
              label={type}
              size="small"
              sx={{
                backgroundColor: getColorByColumnType(type),
                color: "#fff",
                fontWeight: 600,
                fontSize: "0.75rem",
                height: "22px",
              }}
            />
            {index < typesList.length - 1 && (
              <span style={{ margin: "0 4px" }}>{t("common:or")}</span>
            )}
          </React.Fragment>
        ))}
      </Box>
    );
  };

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
      {taskRequirements && !infoLoading && !validationPending && (
        <Alert
          severity={columnsAreValid ? "success" : "error"}
          sx={{
            mb: 2,
            "& .MuiAlert-icon": { fontSize: 24 },
            bgcolor: (theme) =>
              `${theme.palette[columnsAreValid ? "success" : "error"].main}40`,
            border: (theme) =>
              `1px solid ${
                theme.palette[columnsAreValid ? "success" : "error"].main
              }`,
          }}
          data-tour="models-validation-alert"
        >
          <AlertTitle>
            {t(
              columnsAreValid
                ? "experiments:label.columnsValidRequirements"
                : "experiments:label.columnsInvalidRequirements",
              { taskName: taskRequirements.display_name },
            )}
          </AlertTitle>
          <Grid container spacing={4}>
            {["inputs", "outputs"].map((side) =>
              columnGroupsOf(side).map((group, index) => (
                <Grid size={{ xs: 12 }} key={`${side}-${index}`}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 2,
                      flexWrap: "wrap",
                    }}
                  >
                    <Trans
                      i18nKey={
                        side === "inputs"
                          ? "experiments:label.datasetInputColumnRequirements"
                          : "experiments:label.datasetOutputColumnRequirements"
                      }
                    >
                      <span>The columns must be of the types</span>
                      {renderTypesAsChips(group.types)}
                      <span>, and they should have a cardinality of </span>
                      <span>
                        {{ cardinality: describeCardinality(group) }}.
                      </span>
                    </Trans>
                  </Box>
                </Grid>
              )),
            )}
          </Grid>
        </Alert>
      )}

      {!infoLoading ? (
        <Grid container spacing={2}>
          <DivideDatasetColumns
            allColumnNames={datasetInfo.column_names || []}
            columnTypes={datasetTypes}
            selectedInputColumnNames={inputColumnNames}
            onInputColumnNamesChange={setInputColumnNames}
            selectedOutputColumnNames={outputColumnNames}
            onOutputColumnNamesChange={setOutputColumnNames}
            inputError={inputColumnNames.length === 0}
            inputHelperText={
              inputColumnNames.length === 0 ? t("common:required") : ""
            }
            outputError={outputColumnNames.length === 0}
            outputHelperText={
              outputColumnNames.length === 0 ? t("common:required") : ""
            }
            disabled={
              infoLoading || (datasetInfo.column_names || []).length === 0
            }
          />
        </Grid>
      ) : (
        <Box sx={{ display: "flex", justifyContent: "center" }}>
          <CircularProgress />
        </Box>
      )}
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
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  dataset: PropTypes.object.isRequired,
};
export default PrepareDatasetStep;
