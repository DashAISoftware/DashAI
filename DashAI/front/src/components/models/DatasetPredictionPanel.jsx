import React, { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import { Box, Button, CircularProgress } from "@mui/material";
import { ArrowForward } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import DatasetSelector from "../predictions/DatasetSelector";
import {
  createPrediction,
  filterDatasets,
  getPredictions,
} from "../../api/predict";
import { enqueuePredictionJob } from "../../api/job";
import { getDatasets } from "../../api/datasets";
import { getModelSessionById } from "../../api/modelSession";
import { startJobPolling } from "../../utils/jobPoller";

/**
 * DatasetPredictionPanel
 */
export default function DatasetPredictionPanel({
  run,
  session,
  onSaved,
  onClose,
  runRef = null,
  onStateChange = null,
}) {
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [selectedSplit, setSelectedSplit] = useState("all");
  const [modelSession, setModelSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["prediction", "common", "models"]);
  const navigate = useNavigate();

  const handleUploadNewDataset = () => {
    onClose();
    navigate("/app/data/datasets/new");
  };

  const handleRunRef = useRef(null);
  useEffect(() => {
    if (runRef) runRef.current = () => handleRunRef.current?.();
  }, [runRef]);

  useEffect(() => {
    onStateChange?.({
      canRun: !!selectedDataset && !isSubmitting,
      isSubmitting,
    });
  }, [selectedDataset, isSubmitting, onStateChange]);

  useEffect(() => {
    const fetchData = async () => {
      if (!run?.id) return;
      setLoading(true);
      try {
        // Only datasets compatible with the run's model (matching input
        // columns) can be used. A single endpoint validates them all
        // server-side and returns just the valid ids, which we use to filter
        // the already-cheap full dataset list instead of fetching per-dataset
        // info for every candidate up front.
        const [allDatasets, validIds, sessionData] = await Promise.all([
          getDatasets(),
          filterDatasets({ run_id: run.id }),
          getModelSessionById(run.model_session_id || session?.id),
        ]);

        const validIdSet = new Set(validIds.map(String));
        setDatasets(allDatasets.filter((ds) => validIdSet.has(String(ds.id))));
        setModelSession(sessionData);
      } catch (error) {
        console.error("Error loading dataset prediction data:", error);
        enqueueSnackbar(t("prediction:error.loadingPredictionData"), {
          variant: "error",
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [run, session, enqueueSnackbar, t]);

  const handleRunDatasetPrediction = async () => {
    if (!selectedDataset) return;

    setIsSubmitting(true);
    try {
      const prediction = await createPrediction(
        run.id,
        selectedDataset.id,
        selectedSplit !== "all" ? selectedSplit : null,
      );
      const jobResponse = await enqueuePredictionJob(prediction.id);

      if (!jobResponse || !jobResponse.id) {
        throw new Error("Failed to enqueue prediction job");
      }

      enqueueSnackbar(t("prediction:message.predictionJobSubmitted"), {
        variant: "success",
      });

      let optimisticPrediction = prediction;
      try {
        const predictionsAfterEnqueue = await getPredictions(run.id);
        const freshlyCreated = predictionsAfterEnqueue.find(
          (p) => p.id === prediction.id,
        );
        optimisticPrediction = freshlyCreated || prediction;
      } catch (refreshError) {
        console.error(
          "Error refreshing prediction after enqueueing job:",
          refreshError,
        );
      }

      optimisticPrediction = {
        ...optimisticPrediction,
        dataset: optimisticPrediction.dataset || selectedDataset,
        status: optimisticPrediction.status ?? 1,
      };

      if (onSaved) onSaved(optimisticPrediction);
      onClose();

      startJobPolling(
        jobResponse.id,
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
    } catch (error) {
      console.error("Error creating dataset prediction:", error);
      enqueueSnackbar(t("prediction:error.creatingPrediction"), {
        variant: "error",
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  handleRunRef.current = handleRunDatasetPrediction;

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress size={28} />
      </Box>
    );
  }

  if (!modelSession) {
    return null;
  }

  return (
    <Box>
      <DatasetSelector
        experiment={modelSession}
        datasets={datasets}
        selectedDataset={selectedDataset}
        setSelectedDataset={setSelectedDataset}
        runId={run.id}
        onSplitChange={setSelectedSplit}
        actionSlot={
          <Button
            variant="outlined"
            endIcon={<ArrowForward />}
            onClick={handleUploadNewDataset}
            sx={{ textTransform: "none", fontWeight: 500, flexShrink: 0 }}
          >
            {t("models:button.uploadNewDataset")}
          </Button>
        }
      />
    </Box>
  );
}

DatasetPredictionPanel.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number.isRequired,
    model_session_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }).isRequired,
  session: PropTypes.shape({
    id: PropTypes.number,
  }),
  onSaved: PropTypes.func,
  onClose: PropTypes.func.isRequired,
};
