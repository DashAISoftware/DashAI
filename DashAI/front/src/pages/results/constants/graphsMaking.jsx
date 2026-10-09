import { getTraceColors } from "../../../utils/chartColors";

/**
 * Append one run's bar trace to graphsToView.
 *
 * @param {object}  graphsToView  Accumulator object { bar: [] }
 * @param {object}  run           Run data object
 * @param {string[]} metrics      Metric names to plot
 * @param {number[]} values       Corresponding metric values (null if missing)
 * @param {number}  runIndex      Zero-based index used to pick a trace color
 * @param {object}  theme         MUI theme object
 */
function graphsMaking(graphsToView, run, metrics, values, runIndex, theme) {
  graphsToView.bar = graphsToView.bar || [];

  const colors = getTraceColors(theme);
  const color = colors[runIndex % colors.length];
  const runLabel = run.run_name || run.name || `Run ${runIndex + 1}`;

  graphsToView.bar.push({
    type: "bar",
    name: runLabel,
    x: metrics,
    y: values,
    marker: { color, opacity: 0.85 },
  });

  return graphsToView;
}

/**
 * Build one small bar chart PER METRIC (small multiples), instead of a single
 * chart with all metrics grouped on one x-axis. Each metric gets its own
 * scale, so metrics with very different ranges (e.g. Accuracy vs LogLoss)
 * are never forced onto a shared axis. Every run keeps the same color across
 * every panel (identity, not rank) so it stays recognizable throughout.
 *
 * Runs in `hiddenRunIds` are dropped from the plotted bars/axis but still
 * appear (dimmed) in the returned `legend`, so clicking them again can bring
 * them back — colors are assigned from the FULL run list first, so a run's
 * color never shifts when other runs are toggled off/on.
 *
 * @param {object[]} finishedRuns          Array of completed run objects
 * @param {Set}      hiddenRunIds          Run ids currently deselected
 * @param {string[]} metrics               Metric names — one panel each
 * @param {string}   metricsKey            e.g. "test_metrics"
 * @param {object}   theme                 MUI theme object
 * @param {object}   [metricsMetadata={}]  { MetricName: { maximize: bool } }
 * @returns {{ panels: object[], legend: {id: number, label: string, color: string, hidden: boolean}[] }}
 */
function smallMultiplesMaking(
  finishedRuns,
  hiddenRunIds,
  metrics,
  metricsKey,
  theme,
  metricsMetadata = {},
) {
  const MAX_LABEL = 16;
  const truncate = (s) =>
    s.length > MAX_LABEL ? `${s.slice(0, MAX_LABEL)}…` : s;

  const colors = getTraceColors(theme);
  const fullRunLabels = finishedRuns.map(
    (run, idx) => run.run_name || run.name || `Run ${idx + 1}`,
  );
  const runColors = finishedRuns.map((_, idx) => colors[idx % colors.length]);

  const visible = finishedRuns
    .map((run, idx) => ({ run, idx }))
    .filter(({ run }) => !hiddenRunIds.has(run.id));

  // Use numeric slots (not the run name) as the category axis. Two different
  // runs of the same model (e.g. "BaggingClassifier_1"/"_2") often share the
  // same truncated prefix — if the label itself were the category value,
  // Plotly would treat them as the same category and merge their bars.
  const yValues = visible.map((_, i) => i);
  const visibleLabels = visible.map(({ idx }) => fullRunLabels[idx]);
  const visibleTicks = visibleLabels.map(truncate);
  const visibleColors = visible.map(({ idx }) => runColors[idx]);

  const panels = metrics.map((metric) => {
    const isInverse = metricsMetadata[metric]?.maximize === false;
    const values = visible.map(({ run }) => {
      const metricsObj = run[metricsKey] ?? {};
      const v = metricsObj[metric];
      if (v === undefined || v === null) return null;
      if (Array.isArray(v)) return v[v.length - 1]?.value ?? null;
      return typeof v === "number" ? v : null;
    });

    return {
      metric,
      title: isInverse ? `${metric} ↓` : metric,
      data: [
        {
          type: "bar",
          orientation: "h",
          y: yValues,
          x: values,
          customdata: visibleLabels,
          marker: { color: visibleColors, opacity: 0.85 },
          hovertemplate: "%{customdata}<br>%{x:.4f}<extra></extra>",
        },
      ],
    };
  });

  const legend = finishedRuns.map((run, idx) => ({
    id: run.id,
    label: fullRunLabels[idx],
    color: runColors[idx],
    hidden: hiddenRunIds.has(run.id),
  }));

  const yaxis = { tickvals: yValues, ticktext: visibleTicks };

  return { panels, legend, yaxis };
}

/**
 * Build a single Plotly heatmap trace from all runs at once.
 *
 * Each metric column is independently min-max normalized relative to the
 * visible runs, so every metric fills the full color range regardless of its
 * scale. For lower-is-better metrics (maximize=false in metricsMetadata), the
 * normalization is inverted so the lowest raw value maps to the "best" color.
 *
 * Colorscale: orange (primary) = worst → green (secondary) = best.
 *
 * @param {object[]} finishedRuns          Array of completed run objects
 * @param {Set}      hiddenRunIds          Run ids currently deselected
 * @param {string[]} metrics               Metric names (x-axis columns)
 * @param {string}   metricsKey            e.g. "test_metrics"
 * @param {object}   theme                 MUI theme object
 * @param {object}   [metricsMetadata={}]  { MetricName: { maximize: bool } }
 * @returns {object[]}  Array containing one heatmap trace
 */
function heatmapMaking(
  finishedRuns,
  hiddenRunIds,
  metrics,
  metricsKey,
  theme,
  metricsMetadata = {},
) {
  const MAX_LABEL = 20;
  const truncate = (s) =>
    s.length > MAX_LABEL ? `${s.slice(0, MAX_LABEL)}…` : s;

  const visibleRuns = finishedRuns.filter((run) => !hiddenRunIds.has(run.id));

  const runLabels = visibleRuns.map((run, idx) =>
    truncate(run.run_name || run.name || `Run ${idx + 1}`),
  );

  // Raw values matrix [runs × metrics]
  const zRaw = visibleRuns.map((run) => {
    const metricsObj = run[metricsKey] ?? {};
    return metrics.map((m) => {
      const v = metricsObj[m];
      if (v === undefined || v === null) return null;
      if (Array.isArray(v)) return v[v.length - 1]?.value ?? null;
      return typeof v === "number" ? v : null;
    });
  });

  // Per-column min-max normalization.
  // Lower-is-better metrics (maximize===false) are inverted so the best
  // (lowest) value maps to 1 (green) and the worst maps to 0 (orange).
  const zColorByCol = metrics.map((m, mIdx) => {
    const colVals = zRaw.map((row) => row[mIdx]).filter((v) => v !== null);
    const colMin = colVals.length ? Math.min(...colVals) : 0;
    const colMax = colVals.length ? Math.max(...colVals) : 1;
    const range = colMax - colMin;
    const isInverse = metricsMetadata[m]?.maximize === false;
    return zRaw.map((row) => {
      const v = row[mIdx];
      if (v === null) return null;
      const norm = range === 0 ? 0.5 : (v - colMin) / range;
      return isInverse ? 1 - norm : norm;
    });
  });
  // Transpose back to [runs × metrics]
  const zNorm = visibleRuns.map((_, rIdx) =>
    metrics.map((_, mIdx) => zColorByCol[mIdx][rIdx]),
  );

  const annotationText = zRaw.map((row) =>
    row.map((v) => (v !== null ? v.toFixed(4) : "N/A")),
  );

  // X-axis labels: add ↓ arrow for lower-is-better metrics
  const xLabels = metrics.map((m) =>
    metricsMetadata[m]?.maximize === false ? `${m} ↓` : m,
  );

  // error.main dark (#ff8383) / light (#d32f2f); primary.light is #A7C7FF in both modes
  // To use current-mode colors, change the ternary to just `theme.palette.error.main`
  const worstColor =
    theme.palette.mode === "dark" ? theme.palette.error.main : "#ff8383";
  const bestColor = theme.palette.primary.light;

  return [
    {
      type: "heatmap",
      x: xLabels,
      y: runLabels,
      z: zNorm,
      text: annotationText,
      texttemplate: "%{text}",
      textfont: { size: 11, weight: 700, color: theme.palette.text.primary },
      // amber (accent) = min/worst, teal/blue (accent) = max/best
      colorscale: [
        [0, worstColor],
        [1, bestColor],
      ],
      zauto: false,
      zmin: 0,
      zmax: 1,
      showscale: true,
      colorbar: {
        tickmode: "array",
        tickvals: [0, 1],
        ticktext: ["Worst", "Best"],
        tickfont: { color: theme.palette.text.primary },
      },
      hoverongaps: false,
      xgap: 2,
      ygap: 2,
    },
  ];
}

export { heatmapMaking, smallMultiplesMaking };
export default graphsMaking;
