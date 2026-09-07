import React, { useEffect, useMemo, useState } from "react";
import { useStrategyKind } from "../../hooks/useStrategyKind";
import { STRATEGY_KINDS } from "../../utils/splitsPayload";
import PropTypes from "prop-types";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import { useTheme } from "@mui/material/styles";
import { Box, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { PlayArrow, Delete, Visibility } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { useTableLocalization } from "../../utils/useTableLocalization";
import DeleteConfirmationModal from "../threeSectionLayout/DeleteConfirmationModal";
import {
  getComponentDownloadState,
  subscribeAnyDownloadState,
} from "./model/ComponentDownloadControl";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../credentials/credentialStatus";
import { canTrainRun, isRunActive } from "../../utils/runStatus";
import { useModels } from "./ModelsContext";

/**
 * Compact comparison table showing all runs in a session.
 * Renders at its natural content height — the page scrolls, not the table.
 *
 * Scores are computed server-side and fetched from the backend.
 */
function ModelComparisonTable({
  runs: initialRuns = [],
  onTrain,
  onViewDetails,
  onDelete,
  onRowClick,
  metricSplit = "test",
}) {
  const { allModels: models, allMetrics: metrics } = useModels();
  const [runs, setRuns] = useState(initialRuns);
  const [runToDelete, setRunToDelete] = useState(null);
  // Bump to re-render when a download finishes so the train button enables.
  const [, setDownloadVersion] = useState(0);
  // Get the selected session from context to determine if cross-validation is used.
  const { selectedSession } = useModels();

  useEffect(
    () => subscribeAnyDownloadState(() => setDownloadVersion((v) => v + 1)),
    [],
  );

  // Live credential statuses so the train button re-enables the instant a
  // required credential is verified.
  const { statuses: credentialStatuses, loaded: credentialsLoaded } =
    useCredentialStatuses();

  // A run is trainable only if its model needs no download or the download is
  // present and not in progress (live state overrides a stale fetched flag).
  const isModelReady = (modelName) => {
    const model = models.find((m) => m.name === modelName);
    if (!model?.metadata?.requires_download) return true;
    const cached = getComponentDownloadState(modelName);
    const downloaded = cached?.downloaded ?? Boolean(model.downloaded);
    const downloading = Boolean(cached?.downloading);
    return downloaded && !downloading;
  };

  // Whether a run's model still needs its required credentials authenticated.
  const isModelLocked = (modelName) => {
    const model = models.find((m) => m.name === modelName);
    return getComponentCredentialState(
      model || {},
      credentialStatuses,
      credentialsLoaded,
    ).locked;
  };

  const { t } = useTranslation(["models", "common", "credentials"]);
  const theme = useTheme();
  const localization = useTableLocalization();

  // ────────────────────────────────────────────────────────────────────────
  // Sync initial runs prop with local state
  // ────────────────────────────────────────────────────────────────────────

  useEffect(() => {
    setRuns(initialRuns);
  }, [initialRuns]);

  // ────────────────────────────────────────────────────────────────────────
  // Build columns
  // ────────────────────────────────────────────────────────────────────────

  const isCrossValidation =
    useStrategyKind(selectedSession?.evaluation_strategy) === STRATEGY_KINDS.CV;

  // Run type color using existing theme.palette.accent tokens
  const getRunType = (run) => {
    if (run.nested) return "nestedCv";
    if (run.optimizer_name) return "withHpo";
    return "withoutHpo";
  };

  const runTypeStyles = {
    withoutHpo: {
      bg: theme.palette.dataType.default,
      border: theme.palette.dataType.default,
      color: theme.palette.dataType.default,
      label: "Sin HPO",
    },
    withHpo: {
      bg: theme.palette.accent.tealDim,
      border: theme.palette.accent.tealBorder,
      color: theme.palette.accent.teal,
      label: "HPO",
    },
    ...(isCrossValidation
      ? {
          nestedCv: {
            bg: "#585370",
            border: "#585370",
            color: "#585370",
            label: "CV anidado",
          },
        }
      : {}),
  };

  const runTypeLegend = Object.entries(runTypeStyles).map(([key, value]) => ({
    key,
    ...value,
  }));

  const getMetricColumns = () => {
    const metricsSet = new Set();
    const prefix = metricSplit === "validation" ? "val" : metricSplit;

    runs.forEach((run) => {
      const metricsKey = `${metricSplit}_metrics`;
      if (run[metricsKey]) {
        Object.keys(run[metricsKey]).forEach((key) =>
          metricsSet.add(`${prefix}_${key}`),
        );
      }
    });

    // Compute best value per metric field
    const bestValues = {};
    Array.from(metricsSet).forEach((metricField) => {
      const metricName = metricField.replace(/^(test|train|val)_/, "");
      const metricInfo = metrics.find((m) => m.name === metricName);
      const maximize = metricInfo?.metadata?.maximize;
      if (maximize === undefined || maximize === null) return;

      const metricsKey = `${metricSplit}_metrics`;
      const values = runs
        .filter(
          (run) =>
            run[metricsKey]?.[metricName] !== undefined &&
            run[metricsKey]?.[metricName] !== null,
        )
        .map((run) => Number(run[metricsKey][metricName]))
        .filter((v) => !isNaN(v));

      if (values.length > 0) {
        bestValues[metricField] = maximize
          ? Math.max(...values)
          : Math.min(...values);
      }
    });

    return Array.from(metricsSet).map((metricField) => {
      const metricName = metricField.replace(/^(test|train|val)_/, "");
      const metricInfo = metrics.find((m) => m.name === metricName);
      const metricDescription = metricInfo?.description || metricName;
      const maximize = metricInfo?.metadata?.maximize;

      const directionArrow =
        maximize === true ? "↑" : maximize === false ? "↓" : "";
      const directionLabel =
        maximize === true
          ? t("models:label.higherIsBetter")
          : maximize === false
            ? t("models:label.lowerIsBetter")
            : "";

      const tooltipContent = directionLabel
        ? `${metricDescription} — ${directionLabel}`
        : metricDescription;

      const bestVal = bestValues[metricField];
      const metricsKey = `${metricSplit}_metrics`;

      return {
        id: metricField,
        accessorFn: (row) => row[metricsKey]?.[metricName],
        header: `${metricName} ${directionArrow}`.trim(),
        size: 120,
        Header: () => (
          <Tooltip title={tooltipContent} arrow placement="top">
            <Box
              sx={{
                cursor: "help",
                width: "100%",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {metricName}
              {directionArrow && (
                <Box component="span" sx={{ ml: 1, opacity: 0.7 }}>
                  {directionArrow}
                </Box>
              )}
            </Box>
          </Tooltip>
        ),
        Cell: ({ row, cell }) => {
          const { status } = row.original;
          const isRunning = isRunActive(status);

          if (isRunning) return "-";
          const val = cell.getValue();
          if (val === null || val === undefined) return "-";

          const value = Number(val);
          if (isNaN(value)) return val;

          const formatted = value.toFixed(4);
          const isBest =
            bestVal !== undefined && Math.abs(value - bestVal) < 1e-9;

          // Aggregated fold metrics carry a standard deviation; a single
          // score such as the one on the reserved rows does not. Drive the
          // display off the value being there rather than off the strategy.
          const stdValue =
            row.original[`${metricSplit}_metrics_std`]?.[metricName] ?? null;

          return (
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 0.25,
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                {isBest && (
                  <Tooltip title={t("models:label.bestModel")} placement="top">
                    <Box
                      component="span"
                      sx={{ color: "warning.main", lineHeight: 1 }}
                    >
                      ★
                    </Box>
                  </Tooltip>
                )}
                <Box>{formatted}</Box>
              </Box>
              {stdValue !== null && (
                <Box sx={{ fontSize: "0.9em", color: "text.secondary" }}>
                  ±{Number(stdValue).toFixed(4)}
                </Box>
              )}
            </Box>
          );
        },
      };
    });
  };

  const data = useMemo(() => runs, [runs]);

  const columns = useMemo(() => {
    return [
      {
        accessorKey: "name",
        header: t("common:modelName"),
        size: 120,
        Cell: ({ cell }) => (
          <Tooltip title={cell.getValue()} placement="top" arrow>
            <Box
              sx={{
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
                width: "120px",
              }}
            >
              {cell.getValue()}
            </Box>
          </Tooltip>
        ),
      },
      {
        accessorKey: "model_name",
        header: t("common:model"),
        size: 120,
        accessorFn: (row) => {
          const model = models.find((m) => m.name === row.model_name);
          return model?.display_name || row.model_name;
        },
        Cell: ({ cell }) => (
          <Tooltip title={cell.getValue()} placement="top" arrow>
            <Box
              sx={{
                width: "120px",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {cell.getValue()}
            </Box>
          </Tooltip>
        ),
      },
      ...getMetricColumns(),
      {
        id: "actions",
        header: t("common:actions"),
        enableSorting: false,
        enableColumnFilter: false,
        size: 150,
        Cell: ({ row }) => {
          const canTrain = canTrainRun(row.original.status);
          const isRunning = isRunActive(row.original.status);
          const modelReady = isModelReady(row.original.model_name);
          const modelLocked = isModelLocked(row.original.model_name);

          return (
            <Box sx={{ display: "flex", gap: 1 }}>
              <Tooltip
                title={
                  modelLocked
                    ? t("credentials:requiredTooltip", {
                        platform: getComponentCredentialState(
                          models.find(
                            (m) => m.name === row.original.model_name,
                          ) || {},
                          credentialStatuses,
                          credentialsLoaded,
                        ).requiredPlatforms,
                      })
                    : modelReady
                      ? t("common:train")
                      : t("common:componentDownload.mustDownload")
                }
              >
                <span>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      onTrain(runs.find((r) => r.id === row.original.id));
                    }}
                    disabled={!canTrain || !modelReady || modelLocked}
                    color="primary"
                  >
                    <PlayArrow fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>

              <Tooltip title={t("common:viewDetails")}>
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onViewDetails(runs.find((r) => r.id === row.original.id));
                  }}
                  color="default"
                >
                  <Visibility fontSize="small" />
                </IconButton>
              </Tooltip>

              <Tooltip title={t("common:delete")}>
                <span>
                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      setRunToDelete(
                        runs.find((r) => r.id === row.original.id),
                      );
                    }}
                    disabled={isRunning}
                    color="error"
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>
            </Box>
          );
        },
      },
    ];
  }, [
    models,
    metrics,
    runs,
    metricSplit,
    t,
    onTrain,
    onViewDetails,
    onDelete,
    credentialStatuses,
    credentialsLoaded,
  ]);

  const columnOrder = useMemo(
    () => columns.map((col) => col.id ?? col.accessorKey).filter(Boolean),
    [columns],
  );

  const table = useMaterialReactTable({
    columns,
    data,
    mrtTheme: { baseBackgroundColor: theme.palette.background.box },
    muiTablePaperProps: {
      elevation: 0,
      sx: {
        display: "flex",
        flexDirection: "column",
        border: "1px solid",
        borderColor: "divider",
      },
    },
    localization,
    initialState: { density: "compact" },
    enableStickyHeader: false,
    enableRowSelection: false,
    enablePagination: false,
    enableTopToolbar: false,
    enableBottomToolbar: false,
    muiTableBodyCellProps: { sx: { py: 1, whiteSpace: "pre" } },
    muiTableHeadCellProps: { sx: { py: 1 } },
    state: { columnOrder },
    muiTableBodyRowProps: ({ row }) => {
      const runType = getRunType(row.original);
      const { bg, border } = runTypeStyles[runType];
      return {
        onClick: () => {
          if (onRowClick) onRowClick(row.original.id);
        },
        sx: {
          cursor: onRowClick ? "pointer" : "default",
          backgroundColor: bg,
          borderLeft: `3px solid ${border}`,
          "&:hover td": { backgroundColor: "transparent" },
        },
      };
    },
  });

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* Table */}
      <Box sx={{ flex: 1, minHeight: 0 }}>
        <MaterialReactTable table={table} />
      </Box>

      {/* Legend for run types (default, hpo, nestedCv) */}
      <Stack
        direction="row"
        spacing={2}
        sx={{ mt: 1, flexWrap: "wrap", alignItems: "center" }}
      >
        {runTypeLegend.map((item) => (
          <Box
            key={item.key}
            sx={{ display: "flex", alignItems: "center", gap: 0.75 }}
          >
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: "50%",
                backgroundColor: item.bg,
                border: `1px solid ${item.border}`,
              }}
            />
            <Typography variant="body2" color="text.secondary">
              {t(`models:label.${item.key}`)}
            </Typography>
          </Box>
        ))}
      </Stack>

      <DeleteConfirmationModal
        open={Boolean(runToDelete)}
        onClose={() => setRunToDelete(null)}
        onConfirm={() => {
          onDelete(runToDelete);
          setRunToDelete(null);
        }}
        content={t("models:message.confirmDeleteRun")}
      />
    </Box>
  );
}

ModelComparisonTable.propTypes = {
  runs: PropTypes.array.isRequired,
  onTrain: PropTypes.func.isRequired,
  onViewDetails: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onRowClick: PropTypes.func,
  metricSplit: PropTypes.oneOf(["train", "validation", "test"]),
};

export default ModelComparisonTable;
