import React, { useEffect, useRef, useState } from "react";
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
import {
  getPreprocessedColumns as getPreprocessedColumnsRequest,
  validateColumns as validateColumnsRequest,
  updateModelSession as updateModelSessionRequest,
} from "../../../api/modelSession";
import { getComponents as getComponentsRequest } from "../../../api/component";
import { useSnackbar } from "notistack";
import { getColorByColumnType } from "../../../utils";
import { useTranslation } from "react-i18next";
import { Trans } from "react-i18next";

/**
 * Step of the session wizard: pick input/output columns from the session's
 * *current* column set — i.e. after any converters configured in the
 * preprocessing step have been applied — rather than from the raw dataset.
 *
 * This step does not own its own submit button: the wizard's shared footer
 * (CreateSessionSteps.jsx) owns "Atrás"/"Siguiente"/"Crear sesión". Instead,
 * this component hands the wizard a ready-to-call PATCH closure via
 * `onReadyToFinalize`, re-supplied on every render so the wizard always has
 * the latest valid input/output selection, without this component needing
 * to know anything about wizard-level navigation.
 *
 * @param {string|number} modelSessionId id of the model session being created
 * @param {string} taskName name of the task selected for this session
 * @param {object} dataset the raw dataset backing this session (its `id` is
 *   still required by the /validation endpoint's schema)
 * @param {number} refreshTrigger bumped by the wizard every time the user
 *   advances into this step, so the column set is re-read after any converter
 *   applied in the preprocessing step (this component never unmounts)
 * @param {function} setNextEnabled function to enable or disable the wizard's "Next" action
 * @param {function} onReadyToFinalize called with a `() => Promise` closure that PATCHes
 *   the session's final input/output columns, re-supplied whenever the selection changes
 */
function ColumnsStep({
  modelSessionId,
  taskName,
  dataset,
  refreshTrigger,
  setNextEnabled,
  onReadyToFinalize,
}) {
  const [columnTypes, setColumnTypes] = useState({});
  const { enqueueSnackbar } = useSnackbar();
  const [infoLoading, setInfoLoading] = useState(true);
  const { t } = useTranslation(["experiments", "common"]);

  // null means "not fetched yet" — distinct from the empty-but-loaded shape
  // getTaskRequirements falls back to when the task genuinely isn't found.
  // The banner below only renders once this is non-null, otherwise it briefly
  // interpolates its message with blank task name/types/cardinality.
  const [taskRequirements, setTaskRequirements] = useState(null);

  const [inputColumnNames, setInputColumnNames] = useState([]);
  const [outputColumnNames, setOutputColumnNames] = useState([]);

  const [columnsReady, setColumnsReady] = useState(false);
  const [columnsAreValid, setColumnsAreValid] = useState(false);
  // True until the current column selection has actually been checked against
  // the backend at least once — distinct from columnsAreValid=false, so the
  // banner doesn't flash red while columns are still being auto-selected or a
  // check is in flight, only once a real valid/invalid result is known.
  const [validationPending, setValidationPending] = useState(true);

  // Mirror of the current selection, readable from the async fetch below
  // without capturing a stale render closure (the fetch only re-runs on
  // refreshTrigger, so its closure can be several renders old by the time it
  // resolves). Assigned during render, which is safe: it's a pure copy of
  // state this component already rendered.
  const selectionRef = useRef({ input: [], output: [] });
  selectionRef.current = {
    input: inputColumnNames,
    output: outputColumnNames,
  };

  const fetchCurrentColumns = async () => {
    setInfoLoading(true);
    try {
      const { columns } = await getPreprocessedColumnsRequest(modelSessionId);
      setColumnTypes(columns); // { [name]: { type, dtype } }
      const allNames = Object.keys(columns);

      // Converters applied in the previous step can add, rename or drop
      // columns (PCA, feature selectors, text vectorizers...), so anything
      // still selected from a previous visit to this step has to be checked
      // against the freshly-fetched set — keeping a name that no longer
      // exists would silently finalize the session with a column the
      // preprocessed data doesn't have.
      let nextInput = selectionRef.current.input.filter(
        (name) => name in columns,
      );
      let nextOutput = selectionRef.current.output.filter(
        (name) => name in columns,
      );

      // Whatever pruning emptied out gets re-seeded with the same heuristic
      // used on first load (all-but-last as input, last as output), applied
      // to the NEW column set — never re-selecting a column the other side
      // still holds, so re-seeding can't produce an overlapping selection.
      if (nextInput.length === 0 && nextOutput.length === 0) {
        nextInput = allNames.length > 1 ? allNames.slice(0, -1) : allNames;
        nextOutput = allNames.length > 0 ? [allNames[allNames.length - 1]] : [];
      } else if (nextInput.length === 0) {
        nextInput = allNames.filter((name) => !nextOutput.includes(name));
      } else if (nextOutput.length === 0) {
        const candidate = [...allNames]
          .reverse()
          .find((name) => !nextInput.includes(name));
        nextOutput = candidate ? [candidate] : [];
      }

      setInputColumnNames(nextInput);
      setOutputColumnNames(nextOutput);
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

      const currentTask = taskComponents.find((task) => task.name === taskName);
      if (currentTask) {
        setTaskRequirements(currentTask);
      } else {
        enqueueSnackbar(
          t("experiments:error.taskRequirementsNotFound", {
            taskName: taskName,
          }),
        );
        setTaskRequirements({
          name: taskName,
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
      if (!columnTypes || Object.keys(columnTypes).length === 0) {
        setColumnsAreValid(false);
        return;
      }

      if (inputColumnNames.length === 0 || outputColumnNames.length === 0) {
        setColumnsAreValid(false);
        return;
      }

      const validation = await validateColumnsRequest(
        taskName,
        dataset.id, // still required by the endpoint's schema
        inputColumnNames,
        outputColumnNames,
        Number(modelSessionId),
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

  useEffect(() => {
    if (inputColumnNames.length >= 1 && outputColumnNames.length >= 1) {
      setColumnsReady(true);
    } else {
      setColumnsReady(false);
    }
  }, [inputColumnNames, outputColumnNames]);

  useEffect(() => {
    if (columnsReady && columnTypes && Object.keys(columnTypes).length > 0) {
      setValidationPending(true);
      validateColumns();
    } else {
      setColumnsAreValid(false);
      setValidationPending(true);
    }
  }, [columnsReady, inputColumnNames, outputColumnNames, columnTypes]);

  useEffect(() => {
    setNextEnabled(!validationPending && columnsAreValid && columnsReady);
  }, [columnsReady, columnsAreValid, validationPending]);

  useEffect(() => {
    fetchCurrentColumns();
    // refreshTrigger isn't read inside fetchCurrentColumns — it's a pure
    // re-run signal, bumped by CreateSessionSteps every time the wizard
    // advances into this step, so converters applied (or removed) in the
    // preprocessing step since the last visit are reflected here even though
    // this component never unmounts.
  }, [modelSessionId, refreshTrigger]);

  useEffect(() => {
    getTaskRequirements();
  }, []);

  // Re-supplied every time the selection changes so the wizard's "Crear
  // sesión" action always closes over the latest input/output columns,
  // without this component owning any wizard-level navigation itself.
  useEffect(() => {
    onReadyToFinalize(() =>
      updateModelSessionRequest({
        id: modelSessionId,
        formData: {
          input_columns: inputColumnNames,
          output_columns: outputColumnNames,
        },
      }),
    );
  }, [modelSessionId, inputColumnNames, outputColumnNames]);

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
      {taskRequirements && !validationPending && (
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
            <Grid size={{ xs: 12 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  flexWrap: "wrap",
                }}
              >
                <Trans i18nKey="experiments:label.datasetInputColumnRequirements">
                  <span>The input columns must be of the types</span>
                  {renderTypesAsChips(taskRequirements.metadata.inputs_types)}
                  <span>
                    , and they should have a cardinality of
                    <span>
                      {{
                        cardinality:
                          taskRequirements.metadata.inputs_cardinality,
                      }}
                      .
                    </span>
                  </span>
                </Trans>
              </Box>
            </Grid>
            <Grid size={{ xs: 12 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  flexWrap: "wrap",
                }}
              >
                <Trans i18nKey="experiments:label.datasetOutputColumnRequirements">
                  <span>The output columns must be of the types</span>
                  {renderTypesAsChips(taskRequirements.metadata.outputs_types)}
                  <span>
                    , and they should have a cardinality of
                    {{
                      cardinality:
                        taskRequirements.metadata.outputs_cardinality,
                    }}
                    .
                  </span>
                </Trans>
              </Box>
            </Grid>
          </Grid>
        </Alert>
      )}

      {!infoLoading ? (
        <Grid container spacing={2}>
          <DivideDatasetColumns
            allColumnNames={Object.keys(columnTypes)}
            columnTypes={columnTypes}
            selectedInputColumnNames={inputColumnNames}
            onInputColumnNamesChange={setInputColumnNames}
            selectedOutputColumnNames={outputColumnNames}
            onOutputColumnNamesChange={setOutputColumnNames}
            disabled={infoLoading || Object.keys(columnTypes).length === 0}
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

ColumnsStep.propTypes = {
  modelSessionId: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
    .isRequired,
  taskName: PropTypes.string.isRequired,
  dataset: PropTypes.object.isRequired,
  refreshTrigger: PropTypes.number,
  setNextEnabled: PropTypes.func.isRequired,
  onReadyToFinalize: PropTypes.func.isRequired,
};
export default ColumnsStep;
