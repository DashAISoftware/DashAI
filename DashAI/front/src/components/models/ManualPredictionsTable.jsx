import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  Typography,
  CircularProgress,
  IconButton,
  Tooltip,
} from "@mui/material";
import { LoadingButton } from "@mui/lab";
import {
  Close as CloseIcon,
  Delete as DeleteIcon,
  DisabledByDefaultOutlined as SelectRowsIcon,
} from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import DatasetTable from "../notebooks/dataset/DatasetTable";
import DeleteConfirmationModal from "../threeSectionLayout/DeleteConfirmationModal";
import InputField from "../predictions/InputField";
import {
  getDatasetFile,
  getDatasetTypesByFilePath,
  getDatasetTypes,
  getDatasetSample,
} from "../../api/datasets";
import {
  createPrediction,
  deletePrediction,
  getPredictions,
} from "../../api/predict";
import { enqueuePredictionJob } from "../../api/job";
import { getModelSessionById } from "../../api/modelSession";
import { startJobPolling } from "../../utils/jobPoller";
import {
  getTargetDecimals,
  formatPredictionRows,
} from "../../utils/predictionFormat";
import "../shared/leanDatasetTable/leanDatasetTable.css";

// Manual predictions are entered by hand, so each one only ever produces a
// handful of rows — fetching the full result in one call (instead of the
// paginated flow used for dataset predictions) is safe here.
const FETCH_ALL_PAGE_SIZE = 10000;

// Stable reference for the "no columns yet" fallback below — a fresh `[]`
// literal on every render would invalidate the `editableRows` memo that
// depends on it for the entire loading window.
const EMPTY_ARRAY = [];

function applyFilter(rows, filterModel) {
  if (!filterModel?.items?.length) return rows;
  return rows.filter((row) =>
    filterModel.items.every(({ field, operator, value }) => {
      const cell = row[field];
      switch (operator) {
        case "isEmpty":
          return cell === null || cell === undefined || cell === "";
        case "isNotEmpty":
          return cell !== null && cell !== undefined && cell !== "";
        case "equals":
          return String(cell) === String(value);
        case "contains":
          return String(cell ?? "")
            .toLowerCase()
            .includes(String(value ?? "").toLowerCase());
        case "startsWith":
          return String(cell ?? "")
            .toLowerCase()
            .startsWith(String(value ?? "").toLowerCase());
        case "endsWith":
          return String(cell ?? "")
            .toLowerCase()
            .endsWith(String(value ?? "").toLowerCase());
        case "greaterThan":
          return Number(cell) > Number(value);
        case "greaterThanOrEqualTo":
          return Number(cell) >= Number(value);
        case "lessThan":
          return Number(cell) < Number(value);
        case "lessThanOrEqualTo":
          return Number(cell) <= Number(value);
        case "between": {
          const [min, max] = value ?? [];
          const num = Number(cell);
          if (min != null && String(min).trim() !== "" && num < Number(min))
            return false;
          if (max != null && String(max).trim() !== "" && num > Number(max))
            return false;
          return true;
        }
        default:
          return true;
      }
    }),
  );
}

function applySort(rows, sortModel) {
  if (!sortModel?.length) return rows;
  const { id, desc } = sortModel[0];
  const sorted = [...rows].sort((a, b) => {
    const av = a[id];
    const bv = b[id];
    if (av == null && bv == null) return 0;
    if (av == null) return -1;
    if (bv == null) return 1;
    if (typeof av === "number" && typeof bv === "number") return av - bv;
    return String(av).localeCompare(String(bv));
  });
  return desc ? sorted.reverse() : sorted;
}

export default function ManualPredictionsTable({
  run,
  session,
  predictions,
  targetColumn,
  datasetSample,
  onSaved,
  onDelete,
  actionsRef = null,
  onStateChange = null,
}) {
  const { t } = useTranslation(["prediction", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const [allRows, setAllRows] = useState([]);
  const [columnTypes, setColumnTypes] = useState({});
  const [loading, setLoading] = useState(true);

  // Row-selection mode: lets the user pick several finished predictions and
  // delete them all at once, instead of a delete icon sitting on every row.
  const [selectionMode, setSelectionMode] = useState(false);
  const [selectedRowIndices, setSelectedRowIndices] = useState(() => new Set());
  const [bulkDeleteOpen, setBulkDeleteOpen] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  // Selection indices are positions in the filtered+sorted row list that
  // `fetchPage` computes internally - this ref keeps the latest version of
  // that list around so indices can be mapped back to real rows on delete.
  const lastFilteredSortedRef = useRef([]);

  // Session metadata needed to render editable "add row" inputs.
  const [modelSession, setModelSession] = useState(null);
  const [inputTypes, setInputTypes] = useState({});
  const [inputSample, setInputSample] = useState(null);
  const [loadingSession, setLoadingSession] = useState(true);

  // Each entry is `{ key, values, status: "draft" | "pending", predictionId }`.
  // Rows stay in this same array across the whole draft -> pending -> real-row
  // lifecycle so they never have to be removed and re-added elsewhere - once
  // the real row lands in `allRows`, the entry is filtered out of
  // `editableRows` (see below) instead of disappearing and popping back in.
  const [manualEntries, setManualEntries] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const nextEntryKeyRef = useRef(0);

  const finishedPredictions = useMemo(
    () => predictions.filter((p) => p.status === 3),
    [predictions],
  );

  const refetchRows = useCallback(() => {
    if (finishedPredictions.length === 0) {
      setAllRows([]);
      setColumnTypes({});
      setLoading(false);
      return;
    }

    setLoading(true);
    const targetDecimals = getTargetDecimals(datasetSample, targetColumn);

    // Newest prediction first, so it doesn't get pushed out of view.
    const orderedPredictions = [...finishedPredictions].reverse();

    Promise.all(
      orderedPredictions.map((prediction) =>
        getDatasetFile(prediction.results_path, 0, FETCH_ALL_PAGE_SIZE).then(
          (data) => {
            const formatted = formatPredictionRows(
              data.rows ?? [],
              targetColumn,
              targetDecimals,
            );
            return formatted.map((row) => ({
              ...row,
              __predictionId: prediction.id,
            }));
          },
        ),
      ),
    )
      .then((groups) => setAllRows(groups.flat()))
      .catch(() => setAllRows([]))
      .finally(() => setLoading(false));

    getDatasetTypesByFilePath(finishedPredictions[0].results_path)
      .then((types) => setColumnTypes(types))
      .catch(() => {});
  }, [finishedPredictions, targetColumn, datasetSample]);

  useEffect(() => {
    refetchRows();
  }, [refetchRows]);

  // Fetch the model session + input column metadata once, so "Add Row" can
  // render editable fields matching the model's expected input schema.
  useEffect(() => {
    let cancelled = false;
    const fetchSessionData = async () => {
      if (!run) return;
      setLoadingSession(true);
      try {
        const sessionData = await getModelSessionById(
          run.model_session_id || session?.id,
        );
        if (cancelled) return;
        setModelSession(sessionData);
        const [types, sample] = await Promise.all([
          getDatasetTypes(sessionData.dataset_id),
          getDatasetSample(sessionData.dataset_id),
        ]);
        if (cancelled) return;
        setInputTypes(types);
        setInputSample(sample);
      } catch (error) {
        console.error(
          "Error loading session data for manual predictions:",
          error,
        );
      } finally {
        if (!cancelled) setLoadingSession(false);
      }
    };
    fetchSessionData();
    return () => {
      cancelled = true;
    };
  }, [run, session]);

  const inputColumns = modelSession?.input_columns ?? EMPTY_ARRAY;

  const createEmptyRow = useCallback(() => {
    if (!inputSample || inputColumns.length === 0) return {};
    const randomIndex = Math.floor(
      Math.random() * inputSample[inputColumns[0]].length,
    );
    const row = {};
    inputColumns.forEach((col) => {
      const typeInfo = inputTypes[col];
      if (typeInfo?.type === "Image") {
        row[col] = null;
      } else if (
        typeInfo?.type === "Categorical" &&
        typeInfo?.categories?.length > 0
      ) {
        row[col] =
          typeInfo.categories[randomIndex % typeInfo.categories.length];
      } else {
        row[col] = inputSample[col][randomIndex];
      }
    });
    return row;
  }, [inputColumns, inputTypes, inputSample]);

  const handleAddRow = () => {
    const key = `manual-${nextEntryKeyRef.current++}`;
    setManualEntries((prev) => [
      ...prev,
      { key, values: createEmptyRow(), status: "draft" },
    ]);
  };

  const handleDraftChange = useCallback((key, col, value) => {
    setManualEntries((prev) =>
      prev.map((entry) =>
        entry.key === key
          ? { ...entry, values: { ...entry.values, [col]: value } }
          : entry,
      ),
    );
  }, []);

  const handleDeleteDraftRow = (key) => {
    setManualEntries((prev) => prev.filter((entry) => entry.key !== key));
  };

  const draftEntries = useMemo(
    () => manualEntries.filter((entry) => entry.status === "draft"),
    [manualEntries],
  );

  // Once a pending entry's real row shows up in `allRows`, drop it from
  // state - it's already excluded from `editableRows` below by then, so this
  // is just cleanup and never causes a visual gap.
  useEffect(() => {
    setManualEntries((prev) => {
      const next = prev.filter(
        (entry) =>
          entry.status === "draft" ||
          !allRows.some((r) => r.__predictionId === entry.predictionId),
      );
      return next.length === prev.length ? prev : next;
    });
  }, [allRows]);

  const handleRunPrediction = async () => {
    if (draftEntries.length === 0) return;
    setIsRunning(true);
    try {
      // Each draft row becomes its own prediction, so every row can later
      // be viewed/deleted independently.
      const submissions = await Promise.all(
        draftEntries.map(async (entry) => {
          const prediction = await createPrediction(run.id, null);
          const jobResponse = await enqueuePredictionJob(prediction.id, [
            entry.values,
          ]);
          if (!jobResponse || !jobResponse.id) {
            throw new Error("Failed to enqueue prediction job");
          }
          return { entry, prediction, jobId: jobResponse.id };
        }),
      );

      enqueueSnackbar(t("prediction:message.predictionJobSubmitted"), {
        variant: "success",
      });

      // Flip the submitted rows to "pending" in place rather than clearing
      // them, so they stay put (as read-only, spinner rows) until the real
      // row is ready instead of disappearing and popping back in elsewhere.
      setManualEntries((prev) =>
        prev.map((entry) => {
          const match = submissions.find((s) => s.entry.key === entry.key);
          return match
            ? { ...entry, status: "pending", predictionId: match.prediction.id }
            : entry;
        }),
      );

      let predictionsAfterEnqueue = [];
      try {
        predictionsAfterEnqueue = await getPredictions(run.id);
      } catch (refreshError) {
        console.error(
          "Error refreshing predictions after enqueueing jobs:",
          refreshError,
        );
      }

      submissions.forEach(({ entry, prediction, jobId }) => {
        const freshlyCreated = predictionsAfterEnqueue.find(
          (p) => p.id === prediction.id,
        );
        const optimisticPrediction = {
          ...(freshlyCreated || prediction),
          status: (freshlyCreated || prediction).status ?? 1,
        };
        if (onSaved) onSaved(optimisticPrediction);

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
            // This entry will never gain a real row, so it can't rely on the
            // `allRows` cleanup effect - drop it here instead.
            setManualEntries((prev) => prev.filter((e) => e.key !== entry.key));
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
      setIsRunning(false);
    }
  };

  // Add Row / Run Prediction live in the parent's header row (next to the
  // Dataset/Manual sub-selector) instead of this table's own toolbar, so both
  // prediction types look consistent. The parent triggers them through this
  // ref and reads button-disabled state through onStateChange.
  useEffect(() => {
    if (actionsRef) {
      actionsRef.current = {
        addRow: handleAddRow,
        runPrediction: handleRunPrediction,
      };
    }
  });

  useEffect(() => {
    onStateChange?.({
      canAddRow: !loadingSession,
      canRun: draftEntries.length > 0,
      isRunning,
    });
  }, [loadingSession, draftEntries.length, isRunning, onStateChange]);

  const extendedColumnTypes = useMemo(
    () => (Object.keys(columnTypes).length > 0 ? columnTypes : inputTypes),
    [columnTypes, inputTypes],
  );

  const editableRows = useMemo(() => {
    // A pending entry keeps rendering here (instead of being removed) until
    // its real row is actually present in `allRows` - see the cleanup effect
    // above.
    const visible = manualEntries.filter(
      (entry) =>
        entry.status === "draft" ||
        !allRows.some((r) => r.__predictionId === entry.predictionId),
    );
    return visible.map((entry) => ({
      key: entry.key,
      renderCell: (colKey) => {
        if (!inputColumns.includes(colKey)) {
          if (entry.status === "pending") return <CircularProgress size={14} />;
          // No dedicated actions column for draft rows (it looked odd sitting
          // mostly empty next to finished rows) - the target column has no
          // result yet anyway, so the row's own cancel button lives there.
          if (colKey === targetColumn) {
            return (
              <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
                <Tooltip title={t("common:delete")}>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteDraftRow(entry.key)}
                    sx={{ color: "#fff" }}
                  >
                    <CloseIcon sx={{ fontSize: 16 }} />
                  </IconButton>
                </Tooltip>
              </Box>
            );
          }
          return "—";
        }
        if (entry.status === "pending") {
          const value = entry.values[colKey];
          const display =
            value instanceof File ? value.name : String(value ?? "");
          return (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ opacity: 0.7 }}
            >
              {display}
            </Typography>
          );
        }
        return (
          <InputField
            handleChange={handleDraftChange}
            rowIndex={entry.key}
            col={colKey}
            typeInfo={inputTypes[colKey]}
            value={entry.values[colKey]}
            placeholder={inputSample?.[colKey]?.[0]}
          />
        );
      },
    }));
  }, [
    manualEntries,
    allRows,
    inputColumns,
    inputTypes,
    inputSample,
    handleDraftChange,
  ]);

  const fetchPage = useCallback(
    async (page, pageSize, filterModel, sortModel) => {
      let rows = applyFilter(allRows, filterModel);
      rows = applySort(rows, sortModel);
      lastFilteredSortedRef.current = rows;
      const total = rows.length;
      const start = page * pageSize;
      return { rows: rows.slice(start, start + pageSize), total };
    },
    [allRows],
  );

  const handleExitSelectionMode = () => {
    setSelectionMode(false);
    setSelectedRowIndices(new Set());
  };

  const handleBulkDeleteConfirm = async () => {
    const targetIds = [
      ...new Set(
        [...selectedRowIndices]
          .map((index) => lastFilteredSortedRef.current[index]?.__predictionId)
          .filter((id) => id != null),
      ),
    ];
    if (targetIds.length === 0) {
      setBulkDeleteOpen(false);
      return;
    }
    setBulkDeleting(true);
    try {
      await Promise.all(targetIds.map((id) => deletePrediction(id)));
      enqueueSnackbar(
        t("prediction:message.predictionsDeleted", {
          count: targetIds.length,
        }),
        { variant: "success" },
      );
      setBulkDeleteOpen(false);
      handleExitSelectionMode();
      if (onDelete) onDelete();
    } catch (error) {
      console.error("Error deleting selected predictions:", error);
      enqueueSnackbar(t("prediction:error.errorDeletingSelected"), {
        variant: "error",
      });
    } finally {
      setBulkDeleting(false);
    }
  };

  const selectionToolbarActions = selectionMode ? (
    <>
      <LoadingButton
        size="small"
        variant="contained"
        color="error"
        startIcon={<DeleteIcon fontSize="small" />}
        disabled={selectedRowIndices.size === 0}
        loading={bulkDeleting}
        onClick={() => setBulkDeleteOpen(true)}
        sx={{ textTransform: "none", fontWeight: 500 }}
      >
        {t("prediction:button.deleteSelected", {
          count: selectedRowIndices.size,
        })}
      </LoadingButton>
      <Button size="small" onClick={handleExitSelectionMode}>
        {t("common:cancel")}
      </Button>
    </>
  ) : (
    <Tooltip title={t("prediction:label.selectRowsToDelete")}>
      <IconButton size="small" onClick={() => setSelectionMode(true)}>
        <SelectRowsIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  );

  return (
    <Box>
      <DatasetTable
        fetchPage={fetchPage}
        initialPageSize={25}
        deps={[allRows.length]}
        columnTypes={extendedColumnTypes}
        showExportButton={false}
        targetColumn={targetColumn}
        editableRows={editableRows}
        infiniteScroll
        extraActions={selectionToolbarActions}
        enableRowSelection={selectionMode}
        selectedRowIndices={selectedRowIndices}
        onRowSelectionChange={setSelectedRowIndices}
      />

      <DeleteConfirmationModal
        open={bulkDeleteOpen}
        onClose={() => setBulkDeleteOpen(false)}
        onConfirm={handleBulkDeleteConfirm}
        content={t("prediction:label.confirmBulkDeletion", {
          count: selectedRowIndices.size,
        })}
      />
    </Box>
  );
}

ManualPredictionsTable.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number.isRequired,
    model_session_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  }).isRequired,
  session: PropTypes.shape({
    id: PropTypes.number,
  }),
  predictions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      status: PropTypes.number.isRequired,
      created: PropTypes.string,
      results_path: PropTypes.string,
    }),
  ).isRequired,
  targetColumn: PropTypes.string,
  datasetSample: PropTypes.object,
  onSaved: PropTypes.func,
  onDelete: PropTypes.func,
  actionsRef: PropTypes.shape({ current: PropTypes.object }),
  onStateChange: PropTypes.func,
};
