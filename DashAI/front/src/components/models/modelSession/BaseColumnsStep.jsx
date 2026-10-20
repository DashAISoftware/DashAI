import React, { useEffect, useLayoutEffect, useState } from "react";
import PropTypes from "prop-types";
import { Grid } from "@mui/material";
import { useTranslation } from "react-i18next";
import DivideDatasetColumns from "./DivideDatasetColumns";

/**
 * Step of the session wizard shown before preprocessing: pick the output
 * column and the candidate columns, all original dataset columns.
 *
 * The candidates are the columns the preprocessing chain may work on; the
 * model inputs are chosen from what the chain leaves, in the last step. The
 * output is never part of the candidates, so no converter can transform it.
 * Nothing is validated against the task here: a candidate may be of a type
 * the task rejects (e.g. text) precisely because a converter will turn it
 * into something it accepts.
 */
function BaseColumnsStep({
  newExp,
  setNewExp,
  setNextEnabled,
  datasetInfo,
  datasetTypes,
}) {
  const { t } = useTranslation(["models", "common"]);
  const rawColumnNames = datasetInfo.column_names || [];

  const [outputColumnNames, setOutputColumnNames] = useState(
    newExp.output_columns || [],
  );
  const [candidateSelection, setCandidateSelection] = useState(
    newExp.candidate_columns || [],
  );

  // The output is never a candidate, even if it was picked as one before.
  const candidateOptions = rawColumnNames.filter(
    (name) => !outputColumnNames.includes(name),
  );
  const candidates = candidateSelection.filter(
    (name) => !outputColumnNames.includes(name),
  );

  useLayoutEffect(() => {
    // Default the first time the dataset's columns load: the last column is
    // the output and every other one is a candidate.
    if (rawColumnNames.length === 0) return;
    if (outputColumnNames.length === 0 && candidateSelection.length === 0) {
      const output = rawColumnNames[rawColumnNames.length - 1];
      setOutputColumnNames([output]);
      setCandidateSelection(rawColumnNames.filter((name) => name !== output));
    }
  }, [rawColumnNames.join(",")]);

  const ready = candidates.length >= 1 && outputColumnNames.length >= 1;

  useEffect(() => {
    setNewExp((prev) => ({
      ...prev,
      candidate_columns: candidates,
      output_columns: outputColumnNames,
    }));
    setNextEnabled(ready);
  }, [candidates.join(","), outputColumnNames.join(",")]);

  return (
    <Grid container spacing={2}>
      <DivideDatasetColumns
        allColumnNames={rawColumnNames}
        columnTypes={datasetTypes}
        inputOptionNames={candidateOptions}
        inputLabel={t("models:label.candidateColumns")}
        selectedInputColumnNames={candidates}
        onInputColumnNamesChange={setCandidateSelection}
        selectedOutputColumnNames={outputColumnNames}
        onOutputColumnNamesChange={setOutputColumnNames}
        inputError={candidates.length === 0}
        inputHelperText={candidates.length === 0 ? t("common:required") : ""}
        outputError={outputColumnNames.length === 0}
        outputHelperText={
          outputColumnNames.length === 0 ? t("common:required") : ""
        }
        disabled={rawColumnNames.length === 0}
      />
    </Grid>
  );
}

BaseColumnsStep.propTypes = {
  newExp: PropTypes.object.isRequired,
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  datasetInfo: PropTypes.object,
  datasetTypes: PropTypes.object,
};

export default BaseColumnsStep;
