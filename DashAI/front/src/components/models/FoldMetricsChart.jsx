import React, {
  useEffect,
  useRef,
  useState,
  useMemo,
  useCallback,
} from "react";
import PropTypes from "prop-types";
import Plot from "react-plotly.js";
import {
  Box,
  CircularProgress,
  Alert,
  AlertTitle,
  ToggleButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { getFoldMetrics, isRepeatedFoldMetrics } from "../../api/run";
import ResultsGraphsParameters from "../../pages/results/components/ResultsGraphsParameters";
import PillToggleButtonGroup from "../shared/PillToggleButtonGroup";
import PlotActions from "../shared/PlotActions";
import { getTraceColors } from "../../utils/chartColors";

// ─── Pure helpers (defined outside component — stable references) ─────────────

const errorInverse = (x) => {
  const a = 0.147;
  const ln = Math.log(1 - x * x);
  const term1 = 2 / (Math.PI * a) + ln / 2;
  const term2 = ln / a;
  return Math.sign(x) * Math.sqrt(Math.sqrt(term1 * term1 - term2) - term1);
};

const calculateNormalQuantiles = (data) => {
  const sorted = [...data].sort((a, b) => a - b);
  return sorted.map((sample, i) => ({
    sample,
    theoretical:
      Math.sqrt(2) * errorInverse(2 * ((i + 0.5) / sorted.length) - 1),
  }));
};

const computeAveraged = (allRepetitionsData) => {
  const reps = Object.keys(allRepetitionsData).filter((k) =>
    k.startsWith("rep_"),
  );
  if (reps.length === 0) return null;
  const metricNames = Object.keys(allRepetitionsData[reps[0]]);
  return Object.fromEntries(
    metricNames.map((metric) => {
      const nFolds = allRepetitionsData[reps[0]][metric].length;
      return [
        metric,
        Array.from({ length: nFolds }, (_, i) => {
          const vals = reps.map(
            (rep) => allRepetitionsData[rep][metric][i] ?? 0,
          );
          return vals.reduce((a, b) => a + b, 0) / vals.length;
        }),
      ];
    }),
  );
};

const computeConcatenated = (allRepetitionsData) => {
  const reps = Object.keys(allRepetitionsData).filter((k) =>
    k.startsWith("rep_"),
  );
  if (reps.length === 0) return null;
  const metricNames = Object.keys(allRepetitionsData[reps[0]]);
  return Object.fromEntries(
    metricNames.map((metric) => [
      metric,
      reps.flatMap((rep) => allRepetitionsData[rep][metric]),
    ]),
  );
};

// ─── Trace builders (pure functions, defined outside component) ───────────────
// Each builds the trace(s) for a single metric's own panel/plot, mirroring
// the small-multiples approach used by LiveMetricsChart — one metric per
// card instead of every metric overlaid on a single shared axis.

const buildBoxplotTrace = (metricName, values, color) => [
  {
    y: values,
    name: "",
    type: "box",
    boxpoints: "outliers",
    marker: { color },
    hovertemplate: "Value: %{y:.4f}<extra></extra>",
  },
];

const buildLineTrace = (metricName, values, color) => [
  {
    x: Array.from({ length: values.length }, (_, i) => i + 1),
    y: values,
    name: metricName,
    type: "scatter",
    mode: "lines+markers",
    line: { color, width: 2 },
    marker: { size: 6, color },
    hovertemplate: "Fold: %{x}<br>Value: %{y:.4f}<extra></extra>",
  },
];

const buildHistogramTrace = (metricName, values, color) => [
  {
    x: values,
    name: metricName,
    type: "histogram",
    nbinsx: Math.max(5, Math.ceil(Math.sqrt(values.length))),
    marker: { color, opacity: 0.7 },
    hovertemplate: "Count: %{y}<extra></extra>",
  },
];

// Returns null when there isn't enough data for a meaningful Q-Q plot (needs
// the metric skipped rather than rendering an empty/misleading panel).
const buildQQTrace = (metricName, values, color) => {
  if (values.length < 3) return null;

  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  const std = Math.sqrt(
    values.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / values.length,
  );
  const quantileData = calculateNormalQuantiles(values);
  const sampleQ = quantileData.map((q) => q.sample);
  const theoreticalQ = quantileData.map((q) => mean + q.theoretical * std);

  const tMin = Math.min(...theoreticalQ);
  const tMax = Math.max(...theoreticalQ);
  const pad = (tMax - tMin) * 0.1 || 1;

  return [
    {
      x: theoreticalQ,
      y: sampleQ,
      name: metricName,
      type: "scatter",
      mode: "markers",
      marker: { size: 8, color },
      hovertemplate: "Theoretical: %{x:.3f}<br>Sample: %{y:.3f}<extra></extra>",
    },
    {
      x: [tMin - pad, tMax + pad],
      y: [tMin - pad, tMax + pad],
      name: "Reference (Normal)",
      type: "scatter",
      mode: "lines",
      line: { color: "#ff7f0e", dash: "solid", width: 2 },
      hoverinfo: "skip",
      showlegend: false,
    },
  ];
};

// ─── Component ────────────────────────────────────────────────────────────────

export default function FoldMetricsChart({ run }) {
  const theme = useTheme();
  const { t } = useTranslation("models");
  const colors = useMemo(() => getTraceColors(theme), [theme]);

  const [allRepetitionsData, setAllRepetitionsData] = useState(null);
  const [selectedRepetition, setSelectedRepetition] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chartType, setChartType] = useState("boxplot");
  const [foldScope, setFoldScope] = useState("default");
  const [split, setSplit] = useState("TRAIN");
  const [selectedMetrics, setSelectedMetrics] = useState([]);

  const selectedMetricsRef = useRef([]);

  const metricSplit = split.toLowerCase();
  const isNestedCV = !!run.nested;

  // ── Fetch ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!run) return;

    setLoading(true);
    setError(null);

    const controller = new AbortController();

    const fetchFoldMetrics = async () => {
      try {
        const scope = isNestedCV && foldScope === "outer" ? "outer" : "default";
        const data = await getFoldMetrics(run.id, {
          metricSplit,
          scope,
          signal: controller.signal,
        });

        let nextData;
        let nextRepetition;

        if (isRepeatedFoldMetrics(data)) {
          const repKeys = Object.keys(data)
            .filter((key) => key.startsWith("rep_"))
            .sort(
              (a, b) => parseInt(a.split("_")[1]) - parseInt(b.split("_")[1]),
            );

          nextData = data;
          // Keep current repetition if still valid
          const currentRep = selectedRepetition;
          const isValidRep =
            currentRep === "averaged" || repKeys.includes(currentRep);
          nextRepetition = isValidRep ? currentRep : "averaged";
        } else {
          nextData = { rep_0: data };
          nextRepetition = "rep_0";
        }

        setAllRepetitionsData(nextData);
        setSelectedRepetition(nextRepetition);
      } catch (err) {
        if (err.name === "CanceledError" || err.name === "AbortError") return;
        setError(err.response?.data?.detail || "Failed to load fold metrics");
        console.error("Error fetching fold metrics:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchFoldMetrics();

    return () => controller.abort();
    // selectedRepetition intentionally excluded — we only read it as "current value at fetch time"
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run, metricSplit, foldScope, isNestedCV]);

  // ── Derived data ───────────────────────────────────────────────────────────

  // Single source of truth for current fold data (covers all chart types)
  const currentFoldMetrics = useMemo(() => {
    if (!allRepetitionsData || !selectedRepetition) return null;
    if (selectedRepetition === "averaged")
      return computeAveraged(allRepetitionsData);
    return allRepetitionsData[selectedRepetition] ?? null;
  }, [allRepetitionsData, selectedRepetition]);

  // For QQ: concatenate all reps when "averaged", otherwise same as current
  const qqFoldMetrics = useMemo(() => {
    if (!allRepetitionsData || !selectedRepetition) return null;
    if (selectedRepetition === "averaged")
      return computeConcatenated(allRepetitionsData);
    return allRepetitionsData[selectedRepetition] ?? null;
  }, [allRepetitionsData, selectedRepetition]);

  const availableMetrics = useMemo(
    () => (currentFoldMetrics ? Object.keys(currentFoldMetrics).sort() : []),
    [currentFoldMetrics],
  );

  const availableReps = useMemo(
    () =>
      allRepetitionsData
        ? Object.keys(allRepetitionsData)
            .filter((k) => k.startsWith("rep_"))
            .sort(
              (a, b) => parseInt(a.split("_")[1]) - parseInt(b.split("_")[1]),
            )
        : [],
    [allRepetitionsData],
  );

  // ── Selection reconciliation ───────────────────────────────────────────────
  // Fires when availableMetrics changes (new fetch or rep change).
  // Keeps user selection if any of the chosen metrics still exist; otherwise selects all.
  useEffect(() => {
    if (availableMetrics.length === 0) return;
    const valid = selectedMetricsRef.current.filter((m) =>
      availableMetrics.includes(m),
    );
    const next = valid.length > 0 ? valid : availableMetrics;
    selectedMetricsRef.current = next;
    setSelectedMetrics(next);
  }, [availableMetrics]);

  // ── Metric handlers ────────────────────────────────────────────────────────
  const handleToggleMetric = useCallback(
    (name) => {
      const next = selectedMetrics.includes(name)
        ? selectedMetrics.filter((m) => m !== name)
        : availableMetrics.filter((m) =>
            new Set([...selectedMetrics, name]).has(m),
          );
      selectedMetricsRef.current = next;
      setSelectedMetrics(next);
    },
    [selectedMetrics, availableMetrics],
  );

  const handleSelectAll = useCallback(() => {
    selectedMetricsRef.current = availableMetrics;
    setSelectedMetrics(availableMetrics);
  }, [availableMetrics]);

  const handleClearAll = useCallback(() => {
    selectedMetricsRef.current = [];
    setSelectedMetrics([]);
  }, []);

  // ── Panels — one metric per small-multiple card, same approach as
  // LiveMetricsChart's panels (each keeps its own scale instead of sharing a
  // single overlaid axis across metrics of possibly very different ranges).
  const panels = useMemo(() => {
    const fm = chartType === "qq" ? qqFoldMetrics : currentFoldMetrics;
    if (!fm) return [];

    const builder = {
      line: buildLineTrace,
      histogram: buildHistogramTrace,
      qq: buildQQTrace,
      boxplot: buildBoxplotTrace,
    }[chartType];

    return Object.keys(fm)
      .sort()
      .filter((name) => selectedMetrics.includes(name))
      .map((metricName, index) => {
        const color = colors[index % colors.length];
        const data = builder(metricName, fm[metricName], color);
        return data && { metric: metricName, data };
      })
      .filter(Boolean);
  }, [chartType, currentFoldMetrics, qqFoldMetrics, selectedMetrics, colors]);

  // ── Panel layout — shared by every panel of the current chart type ─────────
  const panelLayout = useMemo(() => {
    const { palette, typography } = theme;
    const textColor = palette.text.primary;
    const gridColor = palette.divider;
    const tickfont = { color: textColor, size: 10 };

    const axisTitle = (text) => (text ? { text, standoff: 10 } : undefined);

    const axisTitles = {
      boxplot: { x: undefined, y: t("models:label.metricValue") },
      line: {
        x: t("models:label.foldNumber"),
        y: t("models:label.metricValue"),
      },
      qq: {
        x: t("models:label.theoricalQuantiles"),
        y: t("models:label.sampleQuantiles"),
      },
      histogram: {
        x: t("models:label.metricValue"),
        y: t("models:label.frequency"),
      },
    }[chartType];

    return {
      autosize: true,
      height: 240,
      margin: { l: 50, r: 12, t: 8, b: 45 },
      showlegend: false,
      paper_bgcolor: palette.background.paper,
      plot_bgcolor: palette.background.paper,
      font: { color: textColor, family: typography.fontFamily, size: 11 },
      xaxis: {
        title: axisTitle(axisTitles.x),
        gridcolor: gridColor,
        zerolinecolor: gridColor,
        tickfont,
      },
      yaxis: {
        title: axisTitle(axisTitles.y),
        gridcolor: gridColor,
        tickfont,
        automargin: true,
      },
    };
  }, [theme, chartType, t]);

  // ── Early returns ──────────────────────────────────────────────────────────
  if (!run) {
    return (
      <Alert severity="info">
        <AlertTitle>No Run Selected</AlertTitle>
        Select a run to view fold-level metrics.
      </Alert>
    );
  }

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="warning">
        <AlertTitle>No Fold Data Available</AlertTitle>
        {error} — This run may not use cross-validation.
      </Alert>
    );
  }

  if (!allRepetitionsData || !selectedRepetition) {
    return (
      <Alert severity="info">
        <AlertTitle>No Fold Metrics</AlertTitle>
        No fold-level metrics available for this run.
      </Alert>
    );
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        minHeight: 400,
      }}
    >
      {/* Header row 1 — metric selector (left) / train-test split (right) */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 1.5,
          px: 1.5,
          py: 1,
        }}
      >
        <ResultsGraphsParameters
          currentMetrics={availableMetrics}
          selectedMetrics={selectedMetrics}
          handleToggleMetric={handleToggleMetric}
          handleSelectAll={handleSelectAll}
          handleClearAll={handleClearAll}
        />

        <PillToggleButtonGroup
          value={split}
          onChange={(_, v) => {
            if (v) setSplit(v);
          }}
        >
          <ToggleButton value="TRAIN" sx={{ px: 1.5 }}>
            {t("models:label.train")}
          </ToggleButton>
          {/* A fold is scored on its validation partition; the reserved
              rows produce a single value, with nothing to chart per fold. */}
          <ToggleButton value="VALIDATION" sx={{ px: 1.5 }}>
            {t("models:label.validation")}
          </ToggleButton>
        </PillToggleButtonGroup>
      </Box>

      {/* Header row 2 — chart type (left) / fold scope: default vs outer (right) */}
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 1.5,
          px: 1.5,
          py: 1,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <PillToggleButtonGroup
            value={chartType}
            onChange={(_, v) => {
              if (v) setChartType(v);
            }}
          >
            {[
              {
                value: "boxplot",
                label: "Boxplot",
              },
              {
                value: "line",
                label: t("models:label.lines"),
              },
              {
                value: "qq",
                label: "Q-Q",
              },
              {
                value: "histogram",
                label: t("models:label.histogramPlot"),
              },
            ].map(({ value, label, title }) => (
              <ToggleButton
                key={value}
                value={value}
                title={title}
                sx={{ px: 1.5 }}
              >
                {label}
              </ToggleButton>
            ))}
          </PillToggleButtonGroup>

          {availableReps.length > 1 && (
            <FormControl sx={{ minWidth: 140 }} size="small">
              <InputLabel sx={{ fontSize: "0.85rem" }}>
                {t("models:label.repetition")}
              </InputLabel>
              <Select
                value={selectedRepetition ?? ""}
                label={t("models:label.repetition")}
                onChange={(e) => setSelectedRepetition(e.target.value)}
                sx={{ fontSize: "0.85rem" }}
              >
                <MenuItem value="averaged">
                  {chartType === "qq"
                    ? t("models:label.allRepetitions")
                    : t("models:label.averaged")}
                </MenuItem>
                {availableReps.map((rep) => (
                  <MenuItem key={rep} value={rep}>
                    {t("models:label.repetition")}{" "}
                    {parseInt(rep.split("_")[1]) + 1}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Box>

        {isNestedCV && (
          <PillToggleButtonGroup
            value={foldScope}
            onChange={(_, v) => {
              if (v) setFoldScope(v);
            }}
          >
            <ToggleButton
              value="default"
              title={t("models:message.finalFoldFetch")}
              sx={{ px: 1.5 }}
            >
              {t("models:label.finalFoldFetch")}
            </ToggleButton>
            <ToggleButton
              value="outer"
              title={t("models:message.outerFoldFetch")}
              sx={{ px: 1.5 }}
            >
              {t("models:label.outerFoldFetch")}
            </ToggleButton>
          </PillToggleButtonGroup>
        )}
      </Box>

      {/* Chart panels — one per selected metric */}
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          width: "100%",
          overflowY: "auto",
          p: 0.5,
        }}
      >
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
              gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
            }}
          >
            {panels.map((panel) => {
              let containerEl = null;
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
                      data={panel.data}
                      layout={panelLayout}
                      filename={panel.metric}
                    />
                  </Box>
                  <Plot
                    data={panel.data}
                    layout={panelLayout}
                    useResizeHandler
                    style={{ width: "100%", height: "240px" }}
                    config={{ responsive: true, displayModeBar: false }}
                  />
                </Box>
              );
            })}
          </Box>
        )}
      </Box>
    </Box>
  );
}

FoldMetricsChart.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number.isRequired,
    nested: PropTypes.object.isRequired,
  }).isRequired,
};
