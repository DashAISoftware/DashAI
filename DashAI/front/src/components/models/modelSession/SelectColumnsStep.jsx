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
  buildColumnKeysAndTypes,
} from "./sessionColumnRefs";

/**
 * Step of the session wizard: pick input/output columns. A column can be a
 * raw dataset column, or (when preprocessing is configured) the whole output
 * group of one of the session's converter steps, represented here as a
 * synthetic key (e.g. "__group__0") so the underlying Autocomplete only
 * ever deals with plain strings — the same shape a raw column name has.
 */
function SelectColumnsStep({
  newExp,
  setNewExp,
  setNextEnabled,
  dataset,
  datasetInfo,
  datasetTypes,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["experiments", "models", "common"]);

  const [taskRequirements, setTaskRequirements] = useState(null);

  const rawColumnNames = datasetInfo.column_names || [];

  const {
    allKeys: inputOptionNames,
    columnTypes: columnTypesForSelector,
    optionLabels,
  } = buildColumnKeysAndTypes({
    datasetTypes,
    preprocessing: newExp.preprocessing,
  });

  const [inputSelection, setInputSelection] = useState(() =>
    newExp.input_column_refs && newExp.input_column_refs.length > 0
      ? newExp.input_column_refs.map(refToKey)
      : newExp.input_columns || [],
  );
  const [outputColumnNames, setOutputColumnNames] = useState(
    newExp.output_columns || [],
  );

  const inputColumnRefs = inputSelection.map(keyToRef);
  const rawInputNames = inputSelection.filter((key) => !isGroupKey(key));

  const columnsReady =
    inputSelection.length >= 1 && outputColumnNames.length >= 1;
  const [columnsAreValid, setColumnsAreValid] = useState(false);
  const [validationPending, setValidationPending] = useState(true);

  useEffect(() => {
    // Auto-select sensible defaults the first time the dataset's columns load.
    if (rawColumnNames.length === 0) return;
    if (
      inputSelection.length === 0 &&
      (!newExp.input_columns || newExp.input_columns.length === 0)
    ) {
      setInputSelection(
        rawColumnNames.length > 1
          ? rawColumnNames.slice(0, -1)
          : [rawColumnNames[0]],
      );
    }
    if (
      outputColumnNames.length === 0 &&
      (!newExp.output_columns || newExp.output_columns.length === 0)
    ) {
      setOutputColumnNames([rawColumnNames[rawColumnNames.length - 1]]);
    }
  }, [rawColumnNames.join(",")]);

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
        outputColumnNames.length === 0
      ) {
        setColumnsAreValid(false);
        return;
      }
      const hasGroupRef = inputSelection.some(isGroupKey);
      const converterOutputTypes = Object.fromEntries(
        (newExp.preprocessing || []).map((step, index) => [
          String(index),
          step.outputType || null,
        ]),
      );
      const validation = await validateColumnsRequest(
        newExp.task_name,
        dataset.id,
        hasGroupRef ? rawInputNames : inputSelection,
        outputColumnNames,
        hasGroupRef ? inputColumnRefs : undefined,
        hasGroupRef ? converterOutputTypes : undefined,
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
    if (!columnsReady) {
      setColumnsAreValid(false);
      setValidationPending(false);
      return;
    }
    if (rawColumnNames.length > 0) {
      setValidationPending(true);
      validateColumns();
    }
  }, [columnsReady, inputSelection.join(","), outputColumnNames.join(",")]);

  useEffect(() => {
    if (columnsAreValid && columnsReady) {
      setNewExp({
        ...newExp,
        input_columns: rawInputNames,
        output_columns: outputColumnNames,
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
              `1px solid ${theme.palette[columnsAreValid ? "success" : "error"].main}`,
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
          inputError={inputSelection.length === 0}
          inputHelperText={
            inputSelection.length === 0 ? t("common:required") : ""
          }
          outputError={outputColumnNames.length === 0}
          outputHelperText={
            outputColumnNames.length === 0 ? t("common:required") : ""
          }
          disabled={rawColumnNames.length === 0}
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
};

export default SelectColumnsStep;
