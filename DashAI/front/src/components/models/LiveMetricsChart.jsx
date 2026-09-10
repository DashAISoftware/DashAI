import {
  Box,
  ToggleButton,
  Tooltip,
  Typography,
  Button,
  ButtonGroup,
} from "@mui/material";
import { useTheme, alpha } from "@mui/material/styles";
import Plot from "react-plotly.js";
import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import ResultsGraphsParameters from "../../pages/results/components/ResultsGraphsParameters";
import PillToggleButtonGroup from "../shared/PillToggleButtonGroup";
import PlotActions from "../shared/PlotActions";
import { getTraceColors } from "../../utils/chartColors";
import { useStrategyMetadata } from "../../hooks/useStrategyKind";
import { useModels } from "./ModelsContext";

const SPLITS = ["TRAIN", "VALIDATION", "TEST"];

function toFinalValue(value) {
  const resolved = Array.isArray(value)
    ? (value[value.length - 1]?.value ?? null)
    : value;
  const num = Number(resolved);
  return Number.isNaN(num) ? null : num;
}

// Non-iterative models (e.g. plain scikit-learn ones) never call
// calculate_metrics during training, so the only row the backend ever writes
// for TRAIN/VALIDATION is a single final "LAST" value - the same story TEST
// always has, since it's only ever computed once at the end regardless of
// model. The live-metrics websocket only understands TRIAL/STEP/EPOCH levels,
// so without this fallback that single final value has nowhere to render and
// the tab just shows "no metrics available" even though the value exists.
// Used only for splits with zero real TRIAL/STEP/EPOCH data (see
// `hasAnyRealMetrics` below), so it never overwrites/mixes with a real curve.
function toFallbackBuckets(rawMetrics) {
  if (!rawMetrics) return null;
  const formatted = {};
  for (const metricName in rawMetrics) {
    const value = rawMetrics[metricName];
    formatted[metricName] = Array.isArray(value)
      ? value
      : [{ step: 1, value, timestamp: new Date().toISOString() }];
  }
  if (Object.keys(formatted).length === 0) return null;
  return { TRIAL: formatted, STEP: formatted, EPOCH: formatted };
}

function hasAnyRealMetrics(splitData) {
  if (!splitData) return false;
  return ["TRIAL", "STEP", "EPOCH"].some(
    (lvl) => splitData[lvl] && Object.keys(splitData[lvl]).length > 0,
  );
}

export function LiveMetricsChart({ run, modelSessionDetail = null }) {
  const { t } = useTranslation("models");
  const theme = useTheme();
  const [level, setLevel] = useState(null);
  const [split, setSplit] = useState("TRAIN");
  const [data, setData] = useState({});
  const [selectedMetrics, setSelectedMetrics] = useState([]);
  const [availableMetrics, setAvailableMetrics] = useState({
    TRAIN: [],
    VALIDATION: [],
    TEST: [],
  });

  const selectedMetricsPerSplit = useRef({
    TRAIN: null,
    VALIDATION: null,
    TEST: null,
  });
  const socketRef = useRef(null);

  // When a new training starts, clear all previous metrics. Kept separate
  // from the WebSocket effect below purely for readability — the socket
  // itself still needs to reopen on every status change (see that effect's
  // comment) so this doesn't dedupe or skip re-running.
  useEffect(() => {
    const isStarting = run.status === 1 || run.status === 2;
    if (isStarting) {
      setData({});
      setSelectedMetrics([]);
      selectedMetricsPerSplit.current = {
        TRAIN: null,
        VALIDATION: null,
        TEST: null,
      };
    }
  }, [run.status]);

  useEffect(() => {
    const wsOrigin = new URL(
      process.env.REACT_APP_API_URL || "/",
      window.location.origin,
    ).origin;
    let wsUrl;
    try {
      wsUrl = new URL(`/api/v1/metrics/ws/${run.id}`, wsOrigin);
    } catch (e) {
      console.error("Invalid WebSocket base URL:", wsOrigin, e);
      return;
    }
    if (wsUrl.protocol === "http:") {
      wsUrl.protocol = "ws:";
    } else if (wsUrl.protocol === "https:") {
      wsUrl.protocol = "wss:";
    }
    const ws = new WebSocket(wsUrl.toString());

    ws.onmessage = (event) => {
      const incoming = JSON.parse(event.data);

      setData((prev) => {
        const next = structuredClone(prev);

        for (const splitKey in incoming) {
          if (splitKey === "run_status") continue;
          next[splitKey] ??= {};

          for (const levelKey in incoming[splitKey]) {
            next[splitKey][levelKey] ??= {};

            for (const metricName in incoming[splitKey][levelKey]) {
              const incomingPoints = incoming[splitKey][levelKey][metricName];

              if (!Array.isArray(next[splitKey][levelKey][metricName])) {
                next[splitKey][levelKey][metricName] = [...incomingPoints];
              } else {
                next[splitKey][levelKey][metricName].push(...incomingPoints);
              }
            }
          }
        }

        return next;
      });
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    socketRef.current = ws;

    return () => {
      try {
        ws.close();
      } catch (e) {
        console.log("WebSocket already closed");
      }
    };
  }, [run.id, run.status]);

  // The session detail (with train/validation/test metric names) is fetched
  // once by the parent (useRunResultsData) and passed down, instead of this
  // component independently re-fetching the same /model-session/{id}.
  useEffect(() => {
    if (!modelSessionDetail) return;
    setAvailableMetrics({
      TRAIN: modelSessionDetail.train_metrics ?? [],
      VALIDATION: modelSessionDetail.validation_metrics ?? [],
      TEST: modelSessionDetail.test_metrics ?? [],
    });
  }, [modelSessionDetail]);

  // Fallback bucket per split, built from the run's final metrics rather
  // than the websocket. Only ever read when the split has zero real
  // TRIAL/STEP/EPOCH data (see `splitHasRealData` below), so it never
  // overwrites or mixes with an actual curve.
  const fallbackBySplit = useMemo(
    () => ({
      TRAIN: toFallbackBuckets(run.train_metrics),
      VALIDATION: toFallbackBuckets(run.validation_metrics),
      TEST: toFallbackBuckets(run.test_metrics),
    }),
    [run.train_metrics, run.validation_metrics, run.test_metrics],
  );

  const splitHasRealData = hasAnyRealMetrics(data[split]);
  const splitFallback = fallbackBySplit[split];

  const filteredMetrics = useMemo(() => {
    const metrics = splitHasRealData
      ? (data[split]?.[level] ?? {})
      : (splitFallback?.[level] ?? {});
    const allowedMetrics = availableMetrics[split] ?? [];
    return Object.fromEntries(
      Object.entries(metrics).filter(([name]) => allowedMetrics.includes(name)),
    );
  }, [data, split, level, availableMetrics, splitHasRealData, splitFallback]);

  // Compact final-value summary for whichever split is selected — same
  // numbers shown in the session's comparison table, scoped to the split
  // currently picked here instead of a fixed one.
  const summaryMetrics = useMemo(() => {
    const rawMetrics = run[`${split.toLowerCase()}_metrics`] ?? {};
    return Object.entries(rawMetrics)
      .map(([name, value]) => [name, toFinalValue(value)])
      .filter(([, value]) => value !== null);
  }, [run.train_metrics, run.validation_metrics, run.test_metrics, split]);

  // One small panel per metric — each keeps its own x/y scale instead of
  // sharing a single overlaid axis, same "small multiples" approach used for
  // the session results charts.
  const panels = useMemo(() => {
    const colors = getTraceColors(theme);
    return selectedMetrics.map((metricName, idx) => {
      const points = (filteredMetrics[metricName] ?? [])
        .slice()
        .sort((a, b) => a.step - b.step);
      return {
        metric: metricName,
        x: points.map((p) => p.step),
        y: points.map((p) => p.value),
        color: colors[idx % colors.length],
      };
    });
  }, [selectedMetrics, filteredMetrics, theme]);

  // A split with no real curve at all (e.g. a non-iterative model with no
  // hyperparameter optimization) only ever has a single final value - the
  // fallback exposes it as if every level had that one point, same as the
  // three toggle buttons below already do for a real curve.
  const splitHasFallbackData =
    !splitHasRealData && Object.keys(splitFallback?.TRIAL ?? {}).length > 0;

  const hasTrialData = splitHasRealData
    ? Boolean(data[split]?.TRIAL && Object.keys(data[split].TRIAL).length > 0)
    : splitHasFallbackData;
  const hasStepData = splitHasRealData
    ? Boolean(data[split]?.STEP && Object.keys(data[split].STEP).length > 0)
    : splitHasFallbackData;
  const hasEpochData = splitHasRealData
    ? Boolean(data[split]?.EPOCH && Object.keys(data[split].EPOCH).length > 0)
    : splitHasFallbackData;

  const levelLabel = useMemo(() => {
    if (!level) return "";
    return t(`models:label.${level.toLowerCase()}`);
  }, [level, t]);

  useEffect(() => {
    const currentLevelHasData =
      (level === "TRIAL" && hasTrialData) ||
      (level === "STEP" && hasStepData) ||
      (level === "EPOCH" && hasEpochData);

    if (currentLevelHasData) {
      return;
    }

    if (hasEpochData) setLevel("EPOCH");
    else if (hasStepData) setLevel("STEP");
    else if (hasTrialData) setLevel("TRIAL");
    else setLevel(null);
  }, [split, hasEpochData, hasStepData, hasTrialData, level]);

  const filteredMetricKeys = useMemo(
    () => Object.keys(filteredMetrics).sort().join(","),
    [filteredMetrics],
  );

  useEffect(() => {
    const metricNames = filteredMetricKeys ? filteredMetricKeys.split(",") : [];

    if (metricNames.length === 0) {
      setSelectedMetrics([]);
      return;
    }

    const savedSelection = selectedMetricsPerSplit.current[split];

    if (savedSelection !== null) {
      const validSavedMetrics = savedSelection.filter((m) =>
        metricNames.includes(m),
      );
      setSelectedMetrics(validSavedMetrics);
    } else {
      setSelectedMetrics(metricNames);
    }
  }, [split, level, filteredMetricKeys]);

  const handleToggleMetric = (metric) => {
    const canonicalOrder = Object.keys(filteredMetrics);
    const newSelection = selectedMetrics.includes(metric)
      ? selectedMetrics.filter((m) => m !== metric)
      : canonicalOrder.filter(
          (m) => m === metric || selectedMetrics.includes(m),
        );
    setSelectedMetrics(newSelection);
    selectedMetricsPerSplit.current[split] = newSelection;
  };

  const handleSelectAll = () => {
    const newSelection = Object.keys(filteredMetrics);
    setSelectedMetrics(newSelection);
    selectedMetricsPerSplit.current[split] = newSelection;
  };

  const handleClearAll = () => {
    setSelectedMetrics([]);
    selectedMetricsPerSplit.current[split] = [];
  };

  const handleLevelChange = (newLevel) => {
    setLevel(newLevel);
  };

  // Both strategies score a validation split. A session only produces test
  // metrics when it reserved rows the training never saw, and its configured
  // metric lists are what say so.
  const hasTestSplit = useMemo(() => {
    if (!modelSessionDetail) return true;
    return (modelSessionDetail.test_metrics ?? []).length > 0;
  }, [modelSessionDetail]);

  const strategyName =
    useModels()?.selectedSession?.evaluation_strategy ?? null;
  const strategyMetadata = useStrategyMetadata(strategyName);

  const availableSplits = useMemo(() => {
    const scored = strategyMetadata?.scored_splits;
    const offered = Array.isArray(scored)
      ? SPLITS.filter((name) => scored.includes(name.toLowerCase()))
      : SPLITS;
    const withTest = hasTestSplit
      ? offered
      : offered.filter((name) => name !== "TEST");
    return withTest.length > 0 ? withTest : SPLITS;
  }, [strategyMetadata, hasTestSplit]);

  // Never leave the group pointing at a button that is no longer rendered.
  useEffect(() => {
    setSplit((current) =>
      availableSplits.includes(current) ? current : availableSplits[0],
    );
  }, [availableSplits]);

  return (
    <Box
      sx={{
        p: 2,
        display: "grid",
        gridTemplateColumns: "1fr auto",
        columnGap: 2,
        rowGap: 4,
      }}
    >
      <Box sx={{ gridColumn: "1", gridRow: "1" }}>
        <ResultsGraphsParameters
          currentMetrics={Object.keys(filteredMetrics)}
          selectedMetrics={selectedMetrics}
          handleToggleMetric={handleToggleMetric}
          handleSelectAll={handleSelectAll}
          handleClearAll={handleClearAll}
        />
      </Box>

      {/* Spans every row below it so its containing block covers the whole
          scrollable panel, not just this header row - otherwise it would
          stop sticking as soon as the header row itself scrolls out of view. */}
      <Box
        sx={{
          gridColumn: "2",
          gridRow: "1 / -1",
          justifySelf: "end",
          alignSelf: "start",
          position: "sticky",
          top: 0,
          zIndex: 2,
        }}
      >
        <PillToggleButtonGroup
          value={split}
          onChange={(e, newValue) => {
            if (newValue !== null) setSplit(newValue);
          }}
          sx={{
            bgcolor: (theme) => alpha(theme.palette.ui.box, 0.8),
            backdropFilter: "blur(8px)",
          }}
        >
          {availableSplits.includes("TRAIN") && (
            <ToggleButton value="TRAIN" sx={{ px: 1.5 }}>
              {t("models:label.train")}
            </ToggleButton>
          )}
          {availableSplits.includes("VALIDATION") && (
            <ToggleButton value="VALIDATION" sx={{ px: 1.5 }}>
              {t("models:label.validation")}
            </ToggleButton>
          )}
          {availableSplits.includes("TEST") && (
            <ToggleButton value="TEST" sx={{ px: 1.5 }}>
              {t("models:label.test")}
            </ToggleButton>
          )}
        </PillToggleButtonGroup>
      </Box>

      <Box sx={{ gridColumn: "1 / -1", gridRow: "2", minWidth: 0 }}>
        {summaryMetrics.length > 0 && (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 4,
              mb: 4,
              px: 3,
              py: 2,
              border: 1,
              borderColor: "divider",
              borderRadius: 1,
            }}
          >
            {summaryMetrics.map(([name, value]) => (
              <Box
                key={name}
                sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}
              >
                <Typography variant="caption" color="text.secondary">
                  {name}
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  {value.toFixed(4)}
                </Typography>
              </Box>
            ))}
          </Box>
        )}

        {panels.length === 0 ? (
          <Box
            height={350}
            display="flex"
            alignItems="center"
            justifyContent="center"
            border="1px dashed grey"
          >
            <Typography color="textSecondary">
              {t("models:label.noMetricsAvailableForThisView")}
            </Typography>
          </Box>
        ) : (
          <Box
            sx={{
              display: "grid",
              gap: 3,
              gridTemplateColumns: "repeat(auto-fill, minmax(420px, 1fr))",
            }}
          >
            {panels.map((panel) => {
              let containerEl = null;
              const plotData = [
                {
                  type: "scatter",
                  mode: panel.x.length > 1 ? "lines" : "markers",
                  x: panel.x,
                  y: panel.y,
                  line: {
                    color: panel.color,
                    width: 2,
                    shape: "spline",
                    smoothing: 0.7,
                  },
                  marker: { color: panel.color },
                  hovertemplate: "%{x}: %{y:.4f}<extra></extra>",
                },
              ];
              const plotLayout = {
                autosize: true,
                height: 240,
                margin: { l: 50, r: 12, t: 8, b: 55 },
                showlegend: false,
                paper_bgcolor: theme.palette.background.paper,
                plot_bgcolor: theme.palette.background.paper,
                font: {
                  color: theme.palette.text.primary,
                  family: theme.typography.fontFamily,
                  size: 11,
                },
                xaxis: {
                  title: { text: levelLabel, standoff: 10 },
                  gridcolor: theme.palette.divider,
                  zerolinecolor: theme.palette.divider,
                  tickfont: {
                    color: theme.palette.text.primary,
                    size: 10,
                  },
                },
                yaxis: {
                  gridcolor: theme.palette.divider,
                  tickfont: {
                    color: theme.palette.text.primary,
                    size: 10,
                  },
                  automargin: true,
                },
              };
              return (
                <Box
                  key={panel.metric}
                  ref={(node) => {
                    containerEl = node;
                  }}
                  sx={{
                    border: 1,
                    borderColor: "divider",
                    borderRadius: 1,
                    p: 2,
                    "& .plot-actions": {
                      opacity: 0,
                      transition: "opacity 0.15s ease",
                    },
                    "&:hover .plot-actions, &:focus-within .plot-actions": {
                      opacity: 1,
                    },
                    "@media (hover: none)": {
                      "& .plot-actions": { opacity: 1 },
                    },
                  }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      mb: 1,
                      px: 1,
                    }}
                  >
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {panel.metric}
                    </Typography>
                    <PlotActions
                      getContainer={() => containerEl}
                      data={plotData}
                      layout={plotLayout}
                      filename={panel.metric}
                    />
                  </Box>
                  <Plot
                    data={plotData}
                    layout={plotLayout}
                    useResizeHandler
                    style={{ width: "100%", height: "240px" }}
                    config={{ responsive: true, displayModeBar: false }}
                  />
                </Box>
              );
            })}
          </Box>
        )}

        <Box display="flex" justifyContent="flex-end" mt={2}>
          <ButtonGroup size="small" variant="outlined">
            <Button
              variant={level === "TRIAL" ? "contained" : "outlined"}
              onClick={() => handleLevelChange("TRIAL")}
              disabled={!hasTrialData}
            >
              {t("models:label.trial")}
            </Button>
            <Button
              variant={level === "STEP" ? "contained" : "outlined"}
              onClick={() => handleLevelChange("STEP")}
              disabled={!hasStepData}
            >
              {t("models:label.step")}
            </Button>
            <Button
              variant={level === "EPOCH" ? "contained" : "outlined"}
              onClick={() => handleLevelChange("EPOCH")}
              disabled={!hasEpochData}
            >
              {t("models:label.epoch")}
            </Button>
          </ButtonGroup>
        </Box>
      </Box>
    </Box>
  );
}

export default LiveMetricsChart;
