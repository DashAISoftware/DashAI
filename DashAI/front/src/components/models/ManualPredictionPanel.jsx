import React, { useState, useEffect, useCallback, useRef } from "react";
import PropTypes from "prop-types";
import { Box, CircularProgress, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import ManualInput from "../predictions/ManualInput";
import {
  previewManualPrediction,
  createPrediction,
  getPredictions,
} from "../../api/predict";
import { enqueuePredictionJob } from "../../api/job";
import { getModelSessionById } from "../../api/modelSession";
import { getDatasetTypes, getDatasetSample } from "../../api/datasets";
import { startJobPolling } from "../../utils/jobPoller";

/**
 * ManualPredictionPanel – inline (no modal) panel for manual row-based predictions.
 *
 * The user edits rows directly, clicks "Run Prediction" to preview results
 * synchronously, and optionally clicks "Save" to persist the prediction via
 * the async job queue.
 */
export default function ManualPredictionPanel({
  run,
  session,
  onSaved,
  onClose,
  saveRef = null,
  onStateChange = null,
}) {
  const [manualRows, setManualRows] = useState([]);
  const [modelSession, setModelSession] = useState(null);
  const [types, setTypes] = useState({});
  const [sample, setSample] = useState(null);
  const [loadingSession, setLoadingSession] = useState(true);

  const [previewResults, setPreviewResults] = useState(null); // {columns, rows}
  const [isPreviewing, setIsPreviewing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["prediction", "common"]);

  // Keep saveRef pointing to the latest handleSave
  const handleSaveRef = useRef(null);
  useEffect(() => {
    if (saveRef) saveRef.current = () => handleSaveRef.current?.();
  }, [saveRef]);

  // Notify parent when save-button state changes
  useEffect(() => {
    const allRowsHavePrediction =
      !!previewResults &&
      manualRows.length > 0 &&
      manualRows.every((_, i) => previewResults.rows[i] != null);
    onStateChange?.({
      canSave: allRowsHavePrediction && !isSaving && !isPreviewing,
      isSaving,
    });
  }, [previewResults, isSaving, isPreviewing, manualRows, onStateChange]);

  // Load model session metadata once on mount
  useEffect(() => {
    const fetchSessionData = async () => {
      if (!run) return;
      setLoadingSession(true);
      try {
        const sessionData = await getModelSessionById(
          run.model_session_id || session?.id,
        );
        setModelSession(sessionData);
        const [datasetTypes, datasetSample] = await Promise.all([
          getDatasetTypes(sessionData.dataset_id),
          getDatasetSample(sessionData.dataset_id),
        ]);
        setTypes(datasetTypes);
        setSample(datasetSample);
      } catch (error) {
        console.error("Error loading session data:", error);
        enqueueSnackbar(t("prediction:error.loadingPredictionData"), {
          variant: "error",
        });
      } finally {
        setLoadingSession(false);
      }
    };
    fetchSessionData();
  }, [run, session, enqueueSnackbar, t]);

  const prevRowsRef = useRef([]);

  const handleRowsChange = useCallback((newRows) => {
    const prevRows = prevRowsRef.current;
    prevRowsRef.current = newRows;
    setManualRows(newRows);

    if (newRows.length > prevRows.length) {
      // Row added — keep all existing predictions
      return;
    }

    if (newRows.length < prevRows.length) {
      // Row deleted — remove only that row's prediction
      let deletedIndex = prevRows.length - 1;
      for (let i = 0; i < newRows.length; i++) {
        if (JSON.stringify(prevRows[i]) !== JSON.stringify(newRows[i])) {
          deletedIndex = i;
          break;
        }
      }
      setPreviewResults((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          rows: prev.rows.filter((_, i) => i !== deletedIndex),
        };
      });
      return;
    }

    // Row edited — clear only that row's prediction
    for (let i = 0; i < newRows.length; i++) {
      if (JSON.stringify(prevRows[i]) !== JSON.stringify(newRows[i])) {
        setPreviewResults((prev) => {
          if (!prev) return null;
          const rows = [...prev.rows];
          rows[i] = null;
          return { ...prev, rows };
        });
        break;
      }
    }
  }, []);

  const handleRunPrediction = async () => {
    if (!manualRows || manualRows.length === 0) {
      enqueueSnackbar(t("prediction:error.noRowsToPredict"), {
        variant: "warning",
      });
      return;
    }
    setIsPreviewing(true);
    try {
      const result = await previewManualPrediction(run.id, manualRows);
      setPreviewResults(result);
    } catch (error) {
      console.error("Error previewing prediction:", error);
      enqueueSnackbar(t("prediction:error.previewFailed"), {
        variant: "error",
      });
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleSave = async () => {
    if (!manualRows || manualRows.length === 0) return;
    setIsSaving(true);
    try {
      // Each manually entered row becomes its own prediction, so every row
      // can later be viewed/deleted independently instead of all rows from
      // one submission being tied to a single prediction record.
      const submissions = await Promise.all(
        manualRows.map(async (row) => {
          const prediction = await createPrediction(run.id, null);
          const jobResponse = await enqueuePredictionJob(prediction.id, [row]);
          if (!jobResponse || !jobResponse.id) {
            throw new Error("Failed to enqueue prediction job");
          }
          return { prediction, jobId: jobResponse.id };
        }),
      );

      enqueueSnackbar(t("prediction:message.predictionJobSubmitted"), {
        variant: "success",
      });

      let predictionsAfterEnqueue = [];
      try {
        predictionsAfterEnqueue = await getPredictions(run.id);
      } catch (refreshError) {
        console.error(
          "Error refreshing predictions after enqueueing jobs:",
          refreshError,
        );
      }

      onClose();

      submissions.forEach(({ prediction, jobId }) => {
        const freshlyCreated = predictionsAfterEnqueue.find(
          (p) => p.id === prediction.id,
        );
        const optimisticPrediction = {
          ...(freshlyCreated || prediction),
          status: (freshlyCreated || prediction).status ?? 1,
        };

        // Optimistically call onSaved so the card appears quickly
        if (onSaved) onSaved(optimisticPrediction);

        // Poll in the background to update the card status
        startJobPolling(
          jobId,
          async () => {
            const updatedPredictions = await getPredictions(run.id);
            const updatedPrediction = updatedPredictions.find(
              (p) => p.id === prediction.id,
            );
            enqueueSnackbar(t("prediction:message.predictionCompleted"), {
              variant: "success",
            });
            if (onSaved) onSaved(updatedPrediction || prediction);
          },
          async (result) => {
            console.error("Prediction job failed:", result);
            enqueueSnackbar(
              t("prediction:error.predictionFailed", {
                error: result.error || t("common:unknownError"),
              }),
              { variant: "error" },
            );

            try {
              const updatedPredictions = await getPredictions(run.id);
              const updatedPrediction = updatedPredictions.find(
                (p) => p.id === prediction.id,
              );
              if (onSaved) onSaved(updatedPrediction || prediction);
            } catch (refreshError) {
              console.error(
                "Error refreshing prediction after job failure:",
                refreshError,
              );
            }
          },
        );
      });
    } catch (error) {
      console.error("Error saving predictions:", error);
      enqueueSnackbar(t("prediction:error.creatingPrediction"), {
        variant: "error",
      });
    } finally {
      setIsSaving(false);
    }
  };
  handleSaveRef.current = handleSave;

  if (loadingSession) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
        <CircularProgress size={28} />
      </Box>
    );
  }

  if (!modelSession || !sample || Object.keys(types).length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
        {t("prediction:label.noExperimentDataAvailable")}
      </Typography>
    );
  }

  return (
    <Box>
      {/* Row editor */}
      <ManualInput
        experiment={modelSession}
        loading={false}
        types={types}
        sample={sample}
        manualInputData={manualRows}
        setManualInputData={handleRowsChange}
        predictionResults={previewResults}
        targetColumn={modelSession?.output_columns?.[0]}
        onRun={handleRunPrediction}
        isPreviewing={isPreviewing}
        isSaving={isSaving}
      />
    </Box>
  );
}

ManualPredictionPanel.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number.isRequired,
    model_session_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }).isRequired,
  session: PropTypes.shape({
    id: PropTypes.number,
    task_name: PropTypes.string,
  }),
  onSaved: PropTypes.func,
  onClose: PropTypes.func.isRequired,
};
