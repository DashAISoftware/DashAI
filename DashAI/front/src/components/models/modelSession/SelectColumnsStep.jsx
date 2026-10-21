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
import { getComponents as getComponentsRequest } from "../../../api/component";
import { validateColumns as validateColumnsRequest } from "../../../api/modelSession";
import { useSnackbar } from "notistack";
import { getColorByColumnType } from "../../../utils";
import { useTranslation, Trans } from "react-i18next";
import {
  isGroupKey,
  refToKey,
  keyToRef,
  buildStepDisplayNames,
  stateToOptions,
} from "./sessionColumnRefs";
import usePreprocessingStructure from "./usePreprocessingStructure";

/**
 * Last step of the session wizard: pick the model's input columns (and,
 * without preprocessing, its output column).
 *
 * With preprocessing, the inputs are picked from the estimated dataset
 * state after the whole chain (see usePreprocessingStructure): surviving
 * candidate columns plus what the converters produced, each represented by
 * the synthetic key of the ColumnRef pointing at it, so the underlying
 * Autocomplete only ever deals with plain strings. The output was already
 * chosen in BaseColumnsStep and is shown fixed. Every item of the final
 * state is selected by default.
 *
 * A task without a target (clustering) only picks inputs: the output picker
 * is hidden and the session is created with no output columns.
 */
function SelectColumnsStep({
  newExp,
  setNewExp,
  setNextEnabled,
  dataset,
  datasetInfo,
  datasetTypes,
  requiresTarget = true,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["experiments", "models", "common"]);

  const [taskRequirements, setTaskRequirements] = useState(null);
  const [convertersMeta, setConvertersMeta] = useState({});

  const rawColumnNames = datasetInfo.column_names || [];
  const withPreprocessing = Boolean(newExp.applyPreprocessing);
  const steps = newExp.preprocessing || [];

  const { structure } = usePreprocessingStructure({
    datasetId: withPreprocessing ? dataset.id : undefined,
    candidates: newExp.candidate_columns,
    outputColumns: newExp.output_columns,
    steps,
  });

  const stepDisplayNames = buildStepDisplayNames(steps, convertersMeta);
  const finalOptions = stateToOptions(structure?.final, stepDisplayNames, t);
  const inputOptionNames = withPreprocessing
    ? finalOptions.allKeys
    : rawColumnNames;
  // The output keeps its dataset type; an input takes its type after the
  // chain (e.g. a column cast in place by TypeCast).
  const columnTypesForSelector = withPreprocessing
    ? { ...datasetTypes, ...finalOptions.columnTypes }
    : datasetTypes;
  const optionLabels = withPreprocessing ? finalOptions.optionLabels : {};

  const [inputSelectionState, setInputSelection] = useState(() =>
    newExp.input_column_refs && newExp.input_column_refs.length > 0
      ? newExp.input_column_refs.map(refToKey)
      : newExp.input_columns || [],
  );
  const [outputColumnNames, setOutputColumnNames] = useState(
    newExp.output_columns || [],
  );

  // Only what can still be picked: going back and changing the chain can
  // consume a column picked here before, and turning preprocessing off
  // leaves only original columns.
  const optionsKnown = withPreprocessing
    ? Boolean(structure)
    : rawColumnNames.length > 0;
  const inputSelection = optionsKnown
    ? inputSelectionState.filter((key) => inputOptionNames.includes(key))
    : inputSelectionState;

  const inputColumnRefs = inputSelection.map(keyToRef);
  const rawInputNames = inputSelection.filter((key) => !isGroupKey(key));

  // With preprocessing, the input options and their defaults arrive with the
  // estimated structure, after the step has already rendered: until then an
  // empty or unchecked selection is not a user mistake, so no validation
  // error (alert or "Required") may show. useLayoutEffect cannot hide this
  // gap, since it cannot wait for a network response.
  const awaitingStructure = withPreprocessing && !structure;
  const inputMissing = !awaitingStructure && inputSelection.length === 0;

  // A task with no target has no output column to wait for, which is what
  // keeps the Create button reachable for clustering.
  const effectiveOutputColumns = requiresTarget ? outputColumnNames : [];
  const columnsReady =
    inputSelection.length >= 1 &&
    (!requiresTarget || outputColumnNames.length >= 1) &&
    !awaitingStructure;
  const [columnsAreValid, setColumnsAreValid] = useState(false);
  const [validationPending, setValidationPending] = useState(true);

  useLayoutEffect(() => {
    // Auto-select sensible defaults the first time the dataset's columns
    // load. With preprocessing, the output comes from BaseColumnsStep and
    // the inputs default once the estimated structure arrives (below).
    if (rawColumnNames.length === 0 || withPreprocessing) return;
    if (
      inputSelectionState.length === 0 &&
      (!newExp.input_columns || newExp.input_columns.length === 0)
    ) {
      if (!requiresTarget) {
        // Nothing is reserved as a target, so every column is an input.
        setInputSelection(rawColumnNames);
      } else {
        setInputSelection(
          rawColumnNames.length > 1
            ? rawColumnNames.slice(0, -1)
            : [rawColumnNames[0]],
        );
      }
    }
    if (
      requiresTarget &&
      outputColumnNames.length === 0 &&
      (!newExp.output_columns || newExp.output_columns.length === 0)
    ) {
      setOutputColumnNames([rawColumnNames[rawColumnNames.length - 1]]);
    }
  }, [rawColumnNames.join(",")]);

  useLayoutEffect(() => {
    // With preprocessing, default to everything the chain leaves: the model
    // is usually meant to use the chain's whole result.
    if (!withPreprocessing || !structure) return;
    if (inputSelection.length === 0) {
      setInputSelection(finalOptions.allKeys);
    }
  }, [structure]);

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
        setTaskRequirements({
          name: newExp.task_name,
          metadata: {
            inputs_types: [],
            inputs_cardinality: "",
            outputs_types: [],
            outputs_cardinality: "",
            requires_target: requiresTarget,
          },
        });
      }
    } catch (error) {
      enqueueSnackbar(t("experiments:error.errorFetchingTaskRequirements"));
      console.error("Error fetching task requirements:", error);
    }
  };

  const validateColumns = async () => {
    try {
      if (
        rawColumnNames.length === 0 ||
        inputSelection.length === 0 ||
        (requiresTarget && outputColumnNames.length === 0)
      ) {
        setColumnsAreValid(false);
        return;
      }
      // With preprocessing, the backend types every input from the chain's
      // estimated structure, the same one this step's options come from.
      const validation = await validateColumnsRequest(
        newExp.task_name,
        dataset.id,
        rawInputNames,
        effectiveOutputColumns,
        withPreprocessing ? inputColumnRefs : undefined,
        withPreprocessing ? steps : undefined,
      );
      setColumnsAreValid(validation.dataset_status === "valid");
    } catch (error) {
      enqueueSnackbar(t("experiments:error.errorFetchingColumnsValidation"));
      console.error("Error validating columns:", error);
      setColumnsAreValid(false);
    } finally {
      setValidationPending(false);
    }
  };

  useLayoutEffect(() => {
    if (awaitingStructure) {
      // A pending check, not an invalid selection (see awaitingStructure).
      setColumnsAreValid(false);
      setValidationPending(true);
      return;
    }
    if (!columnsReady) {
      setColumnsAreValid(false);
      setValidationPending(false);
      return;
    }
    if (rawColumnNames.length > 0) {
      setValidationPending(true);
      validateColumns();
    }
  }, [
    columnsReady,
    awaitingStructure,
    inputSelection.join(","),
    outputColumnNames.join(","),
  ]);

  useEffect(() => {
    if (columnsAreValid && columnsReady) {
      setNewExp({
        ...newExp,
        input_columns: rawInputNames,
        output_columns: effectiveOutputColumns,
        input_column_refs: inputColumnRefs,
      });
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [
    columnsAreValid,
    columnsReady,
    inputSelection.join(","),
    outputColumnNames.join(","),
  ]);

  useEffect(() => {
    getTaskRequirements();
  }, []);

  useEffect(() => {
    // Only needed to name the steps in the option labels, disambiguating two
    // of the same converter type (e.g. "Simple Imputer" / "Simple Imputer
    // (2)"), see buildStepDisplayNames.
    let cancelled = false;
    getComponentsRequest({ selectTypes: ["Converter"] })
      .then((data) => {
        if (cancelled) return;
        const byName = Object.fromEntries(
          (data || []).map((component) => [component.name, component]),
        );
        setConvertersMeta(byName);
      })
      .catch((error) =>
        console.error("Failed to fetch converter metadata:", error),
      );
    return () => {
      cancelled = true;
    };
  }, []);

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
            {(requiresTarget ? ["inputs", "outputs"] : ["inputs"]).map((side) =>
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

      <Grid container spacing={2}>
        <DivideDatasetColumns
          allColumnNames={rawColumnNames}
          columnTypes={columnTypesForSelector}
          inputOptionNames={inputOptionNames}
          optionLabels={optionLabels}
          selectedInputColumnNames={inputSelection}
          onInputColumnNamesChange={setInputSelection}
          selectedOutputColumnNames={outputColumnNames}
          onOutputColumnNamesChange={setOutputColumnNames}
          requiresTarget={requiresTarget}
          inputError={inputMissing}
          inputHelperText={inputMissing ? t("common:required") : ""}
          outputError={requiresTarget && outputColumnNames.length === 0}
          outputHelperText={
            requiresTarget && outputColumnNames.length === 0
              ? t("common:required")
              : ""
          }
          disabled={rawColumnNames.length === 0}
          outputDisabled={withPreprocessing}
        />
      </Grid>
    </React.Fragment>
  );
}

SelectColumnsStep.propTypes = {
  newExp: PropTypes.object.isRequired,
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  dataset: PropTypes.object.isRequired,
  datasetInfo: PropTypes.object,
  datasetTypes: PropTypes.object,
  requiresTarget: PropTypes.bool,
};

export default SelectColumnsStep;
