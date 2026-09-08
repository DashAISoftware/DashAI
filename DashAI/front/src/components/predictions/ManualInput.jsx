import React, { useMemo } from "react";

import { Box } from "@mui/system";
import ManualInputForm from "./ManualInputForm";
import { CircularProgress } from "@mui/material";
import { useTranslation } from "react-i18next";
import { atomColumnName } from "../../utils/columnAtoms";

export default function ManualInput({
  experiment,
  loading,
  types,
  sample,
  manualInputData,
  setManualInputData,
  predictionResults = null,
  targetColumn = null,
  onRun = null,
  isPreviewing = false,
  isSaving = false,
  showTarget = true,
  title,
  subtitle,
}) {
  const { t } = useTranslation(["prediction"]);

  // Not `experiment.input_columns`: a converter that adds or renames input
  // columns (e.g. BagOfWords' `bow_<word>`, PCA's `pca0`/`pca1`) means
  // those names only exist inside the session's preprocessed data, never
  // in `types`/`sample` (both always fetched from the raw dataset by every
  // caller) — showing/requiring them here asked the user to fill in
  // columns their actual dataset never has. `types`' own keys are exactly
  // what the raw dataset offers; `targetColumn` (when this caller shows
  // one) is excluded the same way the output column is everywhere else.
  // `targetColumn` may still arrive as a raw column *atom*
  // (`{kind: "column", name}`) from a caller that hasn't normalized it —
  // comparing a raw column-name string against an object never matched, so
  // the target silently stayed in the form the user fills in.
  // `atomColumnName` passes a plain string (and `null`) straight through.
  const targetColumnName = atomColumnName(targetColumn);

  const inputColumns = useMemo(
    () => Object.keys(types).filter((col) => col !== targetColumnName),
    [types, targetColumnName],
  );

  return (
    <Box>
      {loading ? (
        <CircularProgress />
      ) : experiment && Object.keys(types).length > 0 && sample ? (
        <ManualInputForm
          types={types}
          sample={sample}
          inputColumns={inputColumns}
          onSubmit={(values) => console.log("Form submitted:", values)}
          manualInputData={manualInputData}
          setManualInputData={setManualInputData}
          predictionResults={predictionResults}
          targetColumn={targetColumnName}
          onRun={onRun}
          isPreviewing={isPreviewing}
          isSaving={isSaving}
          showTarget={showTarget}
          title={title}
          subtitle={subtitle}
        />
      ) : (
        <div>{t("prediction:label.noExperimentDataAvailable")}</div>
      )}
    </Box>
  );
}
