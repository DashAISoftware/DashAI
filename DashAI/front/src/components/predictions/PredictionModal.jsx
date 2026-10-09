import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Tabs,
  Tab,
  IconButton,
  Typography,
  Chip,
  CircularProgress,
  Divider,
} from "@mui/material";
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  PlayArrow as PlayIcon,
} from "@mui/icons-material";
import ModeSelector from "./ModeSelector";
import DatasetSelector from "./DatasetSelector";
import ResultsTable from "./ResultsTable";
import PredictionsTable from "./PredictionsTable";
import ManualInput from "./ManualInput";
import {
  createPrediction,
  filterDatasets,
  getPredictions,
  deletePrediction,
} from "../../api/predict";
import { getDatasets, exportDatasetCsvByPath } from "../../api/datasets";
import { enqueuePredictionJob } from "../../api/job";
import { getModelSessionById } from "../../api/modelSession";
import { getDatasetTypes, getDatasetSample } from "../../api/datasets";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";

export default function PredictionModal({ isOpen, onClose, run }) {
  const [activeTab, setActiveTab] = useState(0);
  const [predictionMode, setPredictionMode] = useState("dataset");
  const [viewMode, setViewMode] = useState("input");
  const [datasets, setDatasets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const [selectedDataset, setSelectedDataset] = useState(null);
  const [selectedSplit, setSelectedSplit] = useState("all");
  const [manualRows, setManualRows] = useState([]);

  const [predictions, setPredictions] = useState([]);
  const [selectedPrediction, setSelectedPrediction] = useState(null);

  // Experiment-related states
  const [experiment, setExperiment] = useState(null);
  const [types, setTypes] = useState({});
  const [loadingExperiment, setLoadingExperiment] = useState(true);
  const [sample, setSample] = useState(null);

  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["prediction", "common"]);

  // Reset state when modal is closed
  useEffect(() => {
    if (!isOpen) {
      setActiveTab(0);
      setPredictionMode("dataset");
      setViewMode("input");
      setDatasets([]);
      setSelectedDataset(null);
      setSelectedSplit("all");
      setPredictions([]);
      setIsLoading(false);
      setManualRows([]);
      setSelectedPrediction(null);
    }
  }, [isOpen]);

  useEffect(() => {
    // Fetch available datasets for prediction
    const fetchDatasets = async () => {
      if (run) {
        try {
          const [allDatasets, validIds] = await Promise.all([
            getDatasets(),
            filterDatasets({ run_id: run.id }),
          ]);
          const validIdSet = new Set(validIds.map(String));
          setDatasets(
            allDatasets.filter((ds) => validIdSet.has(String(ds.id))),
          );
        } catch (error) {
          console.error("Error fetching datasets:", error);
          enqueueSnackbar(t("prediction:error.fetchingDatasets"), {
            variant: "error",
          });
        }
      }
    };

    // Fetch previous predictions for this run
    const fetchPredictions = async () => {
      if (run) {
        try {
          const preds = await getPredictions(run.id);
          setPredictions(preds);
        } catch (error) {
          console.error("Error fetching predictions:", error);
          enqueueSnackbar(t("prediction:error.loadingPreviousPredictions"), {
            variant: "error",
          });
        }
      }
    };

    // Fetch experiment details
    const fetchExperiment = async () => {
      setLoadingExperiment(true);
      try {
        if (run && run.experiment_id) {
          const experimentData = await getModelSessionById(
            run.model_session_id,
          );
          setExperiment(experimentData);
          const datasetTypes = await getDatasetTypes(experimentData.dataset_id);
          setTypes(datasetTypes);
          const datasetSample = await getDatasetSample(
            experimentData.dataset_id,
          );
          setSample(datasetSample);
        }
      } catch (error) {
        console.error("Error fetching experiment:", error);
      } finally {
        setLoadingExperiment(false);
      }
    };

    fetchPredictions();
    fetchExperiment();
    fetchDatasets();
  }, [run]);

  // Handle prediction execution
  const submitPredictionJob = async () => {
    // 1.- Set loading to true
    setIsLoading(true);

    try {
      // 2.- Create a prediction in database
      const prediction = await createPrediction(
        run.id,
        predictionMode === "dataset" ? selectedDataset.id : null,
        predictionMode === "dataset" && selectedSplit !== "all"
          ? selectedSplit
          : null,
      );

      // 3.- Enqueue prediction job
      await enqueuePredictionJob(
        prediction.id,
        predictionMode === "manual" ? manualRows : null,
      );
      enqueueSnackbar(t("prediction:message.predictionJobSubmitted"), {
        variant: "success",
      });

      // 4.- Change prediction status to Delivered
      prediction.status = 1; // Delivered

      // 5.- Add prediction to the list
      setPredictions([prediction, ...predictions]);

      // 6.- Set selected prediction to the new one and switch tab
      setSelectedPrediction(prediction);
      setActiveTab(1);
    } catch (error) {
      console.error("Error submitting prediction job:", error);
      enqueueSnackbar(t("prediction:error.submittingPredictionJob"), {
        variant: "error",
      });
    } finally {
      // 7.- Set loading to false
      setIsLoading(false);
    }
  };

  // Polling for running prediction results
  useEffect(() => {
    if (!predictions || predictions.length === 0) return;

    // Predictions that are still running
    const pending = predictions.filter(
      (p) =>
        p.status === 1 || // Delivered
        p.status === 2, // Started
    );

    if (pending.length === 0) return;

    const intervals = {};

    pending.forEach((prediction) => {
      intervals[prediction.id] = setInterval(async () => {
        try {
          const updated = (await getPredictions(null, prediction.id))[0];

          // Update predictions list
          setPredictions((prev) =>
            prev.map((p) => (p.id === updated.id ? updated : p)),
          );

          // Update selected prediction if it's the one being polled
          setSelectedPrediction((prev) => {
            if (prev && prev.id === updated.id) {
              return updated;
            }
            return prev;
          });

          const statusText = updated.status;

          // If prediction is completed or failed, stop polling
          if (statusText === 3 || statusText === 4) {
            // Finished or Error
            enqueueSnackbar(
              `${t("prediction:label.prediction")} ${
                updated.id
              } ${statusText.toLowerCase()}.`,
              {
                variant: statusText === 3 ? "success" : "error", // Finished
              },
            );
            clearInterval(intervals[prediction.id]);
            delete intervals[prediction.id];
          }
        } catch (error) {
          console.error("Error polling prediction:", error);
          enqueueSnackbar(t("prediction:error.updatingPredictionStatus"), {
            variant: "error",
          });
        }
      }, 2000); // Every 2 seconds
    });

    // Cleanup
    return () => {
      Object.values(intervals).forEach((interval) => clearInterval(interval));
    };
  }, [predictions]);

  const handleDownload = async (selectedPrediction) => {
    const blob = await exportDatasetCsvByPath(selectedPrediction.results_path);
    const isZip = blob.type === "application/zip";
    const ext = isZip ? "zip" : "csv";
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute(
      "download",
      `${"prediction-" + selectedPrediction.created}.${ext}`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDeletePrediction = async (predictionId) => {
    try {
      await deletePrediction(predictionId);
      setPredictions((prev) =>
        prev.filter((prediction) => prediction.id !== predictionId),
      );
      if (selectedPrediction && selectedPrediction.id === predictionId) {
        setSelectedPrediction(null);
      }
      enqueueSnackbar(t("prediction:message.deletedSuccessfully"), {
        variant: "success",
      });
    } catch (error) {
      console.error("Error deleting prediction:", error);
      enqueueSnackbar(t("prediction:error.errorDeleting"), {
        variant: "error",
      });
    }
  };

  const canPredict = () => {
    if (predictionMode === "dataset") {
      return selectedDataset !== null;
    }
    if (!manualRows || manualRows.length === 0) return false;
    const imageColumns = Object.keys(types).filter(
      (col) => types[col]?.type === "Image",
    );
    if (imageColumns.length > 0) {
      return manualRows.every((row) =>
        imageColumns.every((col) => row[col] instanceof File),
      );
    }
    return true;
  };

  if (!isOpen || !run) return null;

  return (
    <Dialog open={isOpen} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Box>
            <Typography variant="h6">
              {t("prediction:label.modelPrediction")}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {run.model_name.display_name ?? run.model_name.name}
            </Typography>
          </Box>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <Divider />

      <Box
        sx={{
          borderBottom: 1,
          borderColor: "divider",
          px: 6,
        }}
      >
        <Tabs
          centered
          sx={{
            minHeight: "55px",
            "& .MuiTab-root": {
              minHeight: "55px",
              fontSize: "0.85rem",
            },
            "& .MuiTabs-indicator": {
              height: "2px",
            },
          }}
          value={activeTab}
          onChange={(e, newValue) => {
            setActiveTab(newValue);
            setSelectedPrediction(null);
          }}
          onClick={() => setSelectedPrediction(null)}
        >
          <Tab label={t("prediction:label.newPrediction")} />
          <Tab label={t("prediction:label.previousPredictions")} />
        </Tabs>
      </Box>

      <Divider />

      <DialogContent sx={{ height: 800, minHeight: "unset", overflow: "auto" }}>
        {activeTab === 0 && (
          <>
            {viewMode === "input" ? (
              <Box>
                <ModeSelector
                  predictionMode={predictionMode}
                  setPredictionMode={setPredictionMode}
                />
                {predictionMode === "dataset" ? (
                  <DatasetSelector
                    experiment={experiment}
                    datasets={datasets}
                    selectedDataset={selectedDataset}
                    setSelectedDataset={setSelectedDataset}
                    runId={run.id}
                    onSplitChange={setSelectedSplit}
                  />
                ) : (
                  <ManualInput
                    experiment={experiment}
                    loading={loadingExperiment}
                    types={types}
                    sample={sample}
                    manualInputData={manualRows}
                    setManualInputData={setManualRows}
                  />
                )}
              </Box>
            ) : (
              <ResultsTable
                selectedPrediction={selectedPrediction}
                datasetSample={sample}
                targetColumn={experiment?.output_columns?.[0]}
              />
            )}
          </>
        )}

        {activeTab === 1 && (
          <>
            {selectedPrediction ? (
              <Box>
                <ResultsTable
                  selectedPrediction={selectedPrediction}
                  datasetSample={sample}
                  targetColumn={experiment?.output_columns?.[0]}
                />
              </Box>
            ) : (
              <PredictionsTable
                predictions={predictions}
                onItemClick={(item) => {
                  setSelectedPrediction(item);
                }}
                onItemDelete={handleDeletePrediction}
              />
            )}
          </>
        )}
      </DialogContent>

      <DialogActions sx={{ px: 6, py: 4 }}>
        {activeTab === 0 ? (
          <>
            <Button variant="outlined" onClick={onClose}>
              {t("common:close")}
            </Button>
            <Button
              variant="contained"
              onClick={submitPredictionJob}
              disabled={!canPredict() || isLoading}
              startIcon={isLoading && <CircularProgress size={16} />}
            >
              {isLoading
                ? t("prediction:label.predicting")
                : t("prediction:button.runPrediction")}
            </Button>
          </>
        ) : selectedPrediction ? (
          <>
            <Button
              variant="outlined"
              onClick={() => setSelectedPrediction(null)}
            >
              {t("common:back")}
            </Button>
            <Button
              variant="contained"
              disabled={
                selectedPrediction?.status !== 3 // Finished
              }
              startIcon={<DownloadIcon />}
              onClick={() => handleDownload(selectedPrediction)}
            >
              {t("common:downloadCSV")}
            </Button>
          </>
        ) : (
          <Button variant="outlined" onClick={onClose}>
            {t("common:close")}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
