import PropTypes from "prop-types";
import React, { useEffect, useMemo, useState } from "react";
import { Box, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";

import { getComponents } from "../../../api/component";
import { heatmapMaking, smallMultiplesMaking } from "../constants/graphsMaking";
import layoutMaking from "../constants/layoutMaking";
import ResultsGraphsLayout from "./ResultsGraphsLayout";

function ResultsGraphs({
  runs,
  selectedSplit: splitProp = undefined,
  onSplitChange = undefined,
  metrics: metricsProp = null,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();
  const { t } = useTranslation(["models"]);

  // Internal split state — used only when no controlled prop is provided
  const [internalSplit, setInternalSplit] = useState("train");
  const [selectedMetrics, setSelectedMetrics] = useState([]);
  const [chartData, setChartData] = useState({});
  // { MetricName: { maximize: bool } } — fetched once on mount
  const [metricsMetadata, setMetricsMetadata] = useState({});
  // Run ids the user deselected from the legend — excluded from the charts
  // but still listed (dimmed) so they can be toggled back on.
  const [hiddenRunIds, setHiddenRunIds] = useState(() => new Set());

  // Controlled or uncontrolled split
  const selectedSplit = splitProp ?? internalSplit;
  const handleChangeSplit = onSplitChange ?? setInternalSplit;

  // Metric maximize direction — reused from the caller's cache when passed,
  // otherwise fetched once on mount (e.g. when used outside the models module).
  useEffect(() => {
    const applyMetrics = (components) => {
      const meta = {};
      components.forEach((c) => {
        meta[c.name] = c.metadata;
      });
      setMetricsMetadata(meta);
    };

    if (metricsProp) {
      applyMetrics(metricsProp);
      return;
    }

    getComponents({ selectTypes: ["Metric"] })
      .then(applyMetrics)
      .catch((error) => {
        console.error(
          "Failed to fetch metric metadata for results heatmap.",
          error,
        );
        enqueueSnackbar(t("models:error.metricMetadataFetch"), {
          variant: "warning",
        });
      });
  }, [metricsProp, enqueueSnackbar, t]);

  const finishedRuns = useMemo(
    () => runs.filter((r) => r.status === 3),
    [runs],
  );

  const availableMetrics = useMemo(() => {
    const sets = { train: new Set(), validation: new Set(), test: new Set() };
    finishedRuns.forEach((run) => {
      if (run.train_metrics)
        Object.keys(run.train_metrics).forEach((m) => sets.train.add(m));
      if (run.validation_metrics)
        Object.keys(run.validation_metrics).forEach((m) =>
          sets.validation.add(m),
        );
      if (run.test_metrics)
        Object.keys(run.test_metrics).forEach((m) => sets.test.add(m));
    });
    return {
      train: Array.from(sets.train),
      validation: Array.from(sets.validation),
      test: Array.from(sets.test),
    };
  }, [finishedRuns]);

  // Auto-select a split only when running in uncontrolled mode. Train is
  // always the default landing split when entering a session; only fall
  // back to another split if train genuinely has no metrics to show.
  useEffect(() => {
    if (splitProp !== undefined) return;
    if (availableMetrics.train.length > 0) setInternalSplit("train");
    else if (availableMetrics.validation.length > 0)
      setInternalSplit("validation");
    else if (availableMetrics.test.length > 0) setInternalSplit("test");
  }, [availableMetrics, splitProp]);

  useEffect(() => {
    setSelectedMetrics(availableMetrics[selectedSplit] ?? []);
  }, [selectedSplit, availableMetrics]);

  useEffect(() => {
    if (finishedRuns.length === 0 || selectedMetrics.length === 0) {
      setChartData({});
      return;
    }

    try {
      const metricsKey = `${selectedSplit}_metrics`;

      // Bar view: one small chart per metric (small multiples) instead of
      // one combined chart, so metrics with different scales/ranges never
      // share an axis. Every run keeps the same color across all panels.
      const { panels, legend, yaxis } = smallMultiplesMaking(
        finishedRuns,
        hiddenRunIds,
        selectedMetrics,
        metricsKey,
        theme,
        metricsMetadata,
      );

      // Heatmap is a single all-runs trace, unchanged.
      const heatmap = heatmapMaking(
        finishedRuns,
        hiddenRunIds,
        selectedMetrics,
        metricsKey,
        theme,
        metricsMetadata,
      );

      const { generalLayout } = layoutMaking("heatmap", {}, theme);
      setChartData({ generalLayout, bar: panels, legend, yaxis, heatmap });
    } catch (error) {
      enqueueSnackbar(t("models:error.errorProcesingExperimentResults"), {
        variant: "error",
      });
      console.error(error);
    }
  }, [
    finishedRuns,
    hiddenRunIds,
    selectedSplit,
    selectedMetrics,
    theme,
    metricsMetadata,
    enqueueSnackbar,
    t,
  ]);

  // Reset deselected runs whenever the underlying run set changes (e.g. a
  // run is deleted or a new one finishes), so a stale id can't stay hidden.
  useEffect(() => {
    const validIds = new Set(finishedRuns.map((r) => r.id));
    setHiddenRunIds((prev) => {
      const next = new Set([...prev].filter((id) => validIds.has(id)));
      return next.size === prev.size ? prev : next;
    });
  }, [finishedRuns]);

  const handleToggleMetric = (metric) => {
    const canonicalOrder = availableMetrics[selectedSplit] ?? [];
    setSelectedMetrics((prev) => {
      if (prev.includes(metric)) {
        return prev.filter((m) => m !== metric);
      }
      const next = new Set([...prev, metric]);
      return canonicalOrder.filter((m) => next.has(m));
    });
  };
  const handleSelectAll = () =>
    setSelectedMetrics(availableMetrics[selectedSplit] ?? []);
  const handleClearAll = () => setSelectedMetrics([]);

  const handleToggleRun = (runId) => {
    setHiddenRunIds((prev) => {
      const next = new Set(prev);
      if (next.has(runId)) {
        next.delete(runId);
      } else {
        next.add(runId);
      }
      return next;
    });
  };

  if (finishedRuns.length === 0) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 16 }}>
        <Typography color="text.secondary">
          {t("models:label.noCompletedRuns")}
        </Typography>
      </Box>
    );
  }

  const currentMetrics = availableMetrics[selectedSplit] ?? [];

  return (
    <ResultsGraphsLayout
      currentMetrics={currentMetrics}
      selectedMetrics={selectedMetrics}
      handleToggleMetric={handleToggleMetric}
      handleSelectAll={handleSelectAll}
      handleClearAll={handleClearAll}
      chartData={chartData}
      onToggleRun={handleToggleRun}
      sessionId={finishedRuns[0]?.model_session_id}
    />
  );
}

ResultsGraphs.propTypes = {
  runs: PropTypes.array.isRequired,
  selectedSplit: PropTypes.string,
  onSplitChange: PropTypes.func,
  metrics: PropTypes.array,
};

export default ResultsGraphs;
