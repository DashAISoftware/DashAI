import React from "react";

import { Box } from "@mui/system";
import ManualInputForm from "./ManualInputForm";
import { CircularProgress } from "@mui/material";
import { useTranslation } from "react-i18next";

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

  return (
    <Box>
      {loading ? (
        <CircularProgress />
      ) : experiment && Object.keys(types).length > 0 && sample ? (
        <ManualInputForm
          types={types}
          sample={sample}
          inputColumns={experiment.input_columns}
          onSubmit={(values) => console.log("Form submitted:", values)}
          manualInputData={manualInputData}
          setManualInputData={setManualInputData}
          predictionResults={predictionResults}
          targetColumn={targetColumn}
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
