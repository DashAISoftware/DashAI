import React, { useState, useRef, useLayoutEffect } from "react";
import { Box, Typography, CardContent, Alert, Button } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import InfoIcon from "@mui/icons-material/Info";
import Plot from "react-plotly.js";
import { StatBox } from "../StatBox";
import { MetricRow } from "../MetricRow";
import ExportableCard from "../ExportableCard";
import { Trans, useTranslation } from "react-i18next";

const BATCH_SIZE = 10;

export const NumericTab = ({
  numericStats,
  scrollToColumn,
  setScrollToColumn,
}) => {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const entries = Object.entries(numericStats ?? {});
  const [visibleCount, setVisibleCount] = useState(BATCH_SIZE);
  const visibleEntries = entries.slice(0, visibleCount);
  const remaining = entries.length - visibleCount;
  const pendingScrollRef = useRef(null);

  useLayoutEffect(() => {
    if (!scrollToColumn) {
      if (!pendingScrollRef.current) return;
      const col = pendingScrollRef.current;
      const card = document.querySelector(`[data-column-card="${col}"]`);
      if (!card) return;
      pendingScrollRef.current = null;
      card.scrollIntoView({ behavior: "smooth", block: "center" });
      card.style.transition = "box-shadow 0.3s";
      card.style.boxShadow = `0 0 0 2px ${theme.palette.warning.main}`;
      setTimeout(() => {
        card.style.boxShadow = "";
      }, 2000);
      return;
    }
    const idx = entries.findIndex(([col]) => col === scrollToColumn);
    if (idx === -1) return;
    if (idx >= visibleCount) {
      pendingScrollRef.current = scrollToColumn;
      setVisibleCount(idx + 1);
    } else {
      const card = document.querySelector(
        `[data-column-card="${scrollToColumn}"]`,
      );
      if (card) {
        card.scrollIntoView({ behavior: "smooth", block: "center" });
        card.style.transition = "box-shadow 0.3s";
        card.style.boxShadow = `0 0 0 2px ${theme.palette.warning.main}`;
        setTimeout(() => {
          card.style.boxShadow = "";
        }, 2000);
      }
    }
    setScrollToColumn(null);
  }, [scrollToColumn, visibleCount]);

  const toNumberOrNull = (value) => {
    if (
      value === null ||
      value === undefined ||
      (typeof value === "string" && value.trim() === "")
    ) {
      return null;
    }

    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  };

  const formatNumber = (value, decimals = 2) => {
    const parsed = toNumberOrNull(value);
    return parsed === null ? "N/A" : parsed.toFixed(decimals);
  };

  return (
    <Box display="flex" flexDirection="column" gap={8}>
      {visibleEntries.map(([column, stats]) => (
        <ExportableCard
          key={column}
          filename={`numeric_${column}`}
          exportData={{ column, ...stats }}
          data-column-card={column}
          sx={{ borderRadius: 2 }}
        >
          <CardContent sx={{ bgcolor: theme.palette.ui.box }}>
            {/* Title */}
            <Box display="flex" alignItems="center" mb={4}>
              <TrendingUpIcon sx={{ color: "primary.main", mr: 2 }} />
              <Typography variant="h6" fontWeight="bold">
                {column}
              </Typography>
            </Box>

            {/* Summary Stats */}
            <Box display="flex" flexWrap="wrap" gap={4} mb={6}>
              <Box flex="1 1 200px" minWidth="150px">
                <StatBox
                  label={t("datasets:label.mean")}
                  value={formatNumber(stats?.mean)}
                />
              </Box>
              <Box flex="1 1 200px" minWidth="150px">
                <StatBox
                  label={t("datasets:label.median")}
                  value={formatNumber(stats?.median)}
                />
              </Box>
              <Box flex="1 1 200px" minWidth="150px">
                <StatBox
                  label={t("datasets:label.stdDev")}
                  value={formatNumber(stats?.std)}
                />
              </Box>
              <Box flex="1 1 200px" minWidth="150px">
                <StatBox
                  label={t("datasets:label.unique")}
                  value={stats?.n_unique ?? "N/A"}
                />
              </Box>
            </Box>

            {/* Two-column metrics */}
            <Box display="flex" flexWrap="wrap" gap={8}>
              {/* Distribution Metrics */}
              <Box flex="1 1 300px" minWidth="250px">
                <Typography
                  variant="body1"
                  fontWeight="bold"
                  color="text.primary"
                  gutterBottom
                  sx={{ textTransform: "uppercase" }}
                >
                  {t("datasets:label.distributionMetrics")}
                </Typography>
                <Box display="flex" flexDirection="column" gap={2}>
                  <MetricRow
                    label={t("datasets:label.lowerBound")}
                    value={formatNumber(stats?.lower_bound)}
                  />
                  <MetricRow
                    label={t("datasets:label.q1")}
                    value={formatNumber(stats?.q1)}
                  />
                  <MetricRow
                    label={t("datasets:label.median")}
                    value={formatNumber(stats?.median)}
                  />
                  <MetricRow
                    label={t("datasets:label.q3")}
                    value={formatNumber(stats?.q3)}
                  />
                  <MetricRow
                    label={t("datasets:label.upperBound")}
                    value={formatNumber(stats?.upper_bound)}
                  />
                  <MetricRow
                    label={t("datasets:label.min")}
                    value={formatNumber(stats?.min)}
                  />
                  <MetricRow
                    label={t("datasets:label.max")}
                    value={formatNumber(stats?.max)}
                  />
                </Box>
              </Box>

              {/* Shape Indicators */}
              <Box flex="1 1 300px" minWidth="250px">
                <Typography
                  variant="body1"
                  fontWeight="bold"
                  color="text.primary"
                  gutterBottom
                  sx={{ textTransform: "uppercase" }}
                >
                  {t("datasets:label.shapeIndicators")}
                </Typography>
                <Box display="flex" flexDirection="column" gap={2}>
                  <MetricRow
                    label={t("datasets:label.skewness")}
                    value={formatNumber(stats?.skew, 3)}
                  />
                  <MetricRow
                    label={t("datasets:label.kurtosis")}
                    value={formatNumber(stats?.kurtosis, 3)}
                  />
                  <MetricRow
                    label={t("datasets:label.outliers")}
                    value={stats?.outliers_count ?? "N/A"}
                  />
                  <MetricRow
                    label={t("datasets:label.range")}
                    value={(() => {
                      const upperBound = toNumberOrNull(stats?.upper_bound);
                      const lowerBound = toNumberOrNull(stats?.lower_bound);

                      return upperBound !== null && lowerBound !== null
                        ? (upperBound - lowerBound).toFixed(2)
                        : "N/A";
                    })()}
                  />
                </Box>
              </Box>
            </Box>

            {/* Horizontal Boxplot Visualization */}
            <Box mt={8}>
              <Typography
                variant="subtitle2"
                color="text.secondary"
                gutterBottom
              >
                {t("datasets:label.boxplot")}
              </Typography>
              {(() => {
                const q1 = toNumberOrNull(stats?.q1);
                const median = toNumberOrNull(stats?.median);
                const q3 = toNumberOrNull(stats?.q3);
                const lowerBound = toNumberOrNull(stats?.lower_bound);
                const upperBound = toNumberOrNull(stats?.upper_bound);
                const min = toNumberOrNull(stats?.min);
                const max = toNumberOrNull(stats?.max);

                const hasBoxplotData =
                  q1 !== null &&
                  median !== null &&
                  q3 !== null &&
                  lowerBound !== null &&
                  upperBound !== null;

                if (!hasBoxplotData) {
                  return null;
                }

                const hasLowerOutlier = min !== null && min < lowerBound;
                const hasUpperOutlier = max !== null && max > upperBound;

                const boxTrace = {
                  q1: [q1],
                  median: [median],
                  q3: [q3],
                  lowerfence: [lowerBound],
                  upperfence: [upperBound],
                  y: [column],
                  type: "box",
                  name: column,
                  orientation: "h",
                  boxpoints: false,
                  marker: { color: theme.palette.info.main },
                  line: { color: theme.palette.text.secondary },
                  fillcolor: theme.palette.info.main,
                  opacity: 0.6,
                  showlegend: false,
                  hoverinfo: "skip",
                };

                const boxHoverTraces = [
                  {
                    x: upperBound,
                    label: t("datasets:label.upperBound"),
                  },
                  { x: q3, label: t("datasets:label.q3") },
                  { x: median, label: t("datasets:label.median") },
                  { x: q1, label: t("datasets:label.q1") },
                  {
                    x: lowerBound,
                    label: t("datasets:label.lowerBound"),
                  },
                ].map(({ x, label }) => ({
                  x: [x],
                  y: [column],
                  type: "scatter",
                  mode: "markers",
                  marker: { opacity: 0, size: 10 },
                  hovertemplate: `${label}: ${formatNumber(x)}<extra></extra>`,
                  showlegend: false,
                }));

                const lowerOutlierTrace = hasLowerOutlier
                  ? {
                      x: [min],
                      y: [column],
                      type: "scatter",
                      mode: "markers",
                      marker: {
                        color: theme.palette.warning.main,
                        size: 8,
                        symbol: "circle-open",
                      },
                      hovertemplate: `Min: ${formatNumber(min)}<extra></extra>`,
                      showlegend: false,
                    }
                  : null;

                const upperOutlierTrace = hasUpperOutlier
                  ? {
                      x: [max],
                      y: [column],
                      type: "scatter",
                      mode: "markers",
                      marker: {
                        color: theme.palette.warning.main,
                        size: 8,
                        symbol: "circle-open",
                      },
                      hovertemplate: `Max: ${formatNumber(max)}<extra></extra>`,
                      showlegend: false,
                    }
                  : null;

                const plotData = [
                  boxTrace,
                  ...boxHoverTraces,
                  lowerOutlierTrace,
                  upperOutlierTrace,
                ].filter(Boolean);

                return (
                  <Plot
                    data={plotData}
                    layout={{
                      paper_bgcolor: "transparent",
                      plot_bgcolor: "transparent",
                      font: { color: theme.palette.text.primary },
                      margin: { t: 10, b: 40, l: 40, r: 20 },
                      height: 220,
                      xaxis: {
                        title: "",
                        zeroline: false,
                        gridcolor:
                          theme.palette.mode === "dark"
                            ? theme.palette.ui.borderLight
                            : theme.palette.ui.border,
                      },
                      yaxis: {
                        showticklabels: false,
                      },
                    }}
                    config={{
                      responsive: true,
                      displayModeBar: false,
                    }}
                    style={{ width: "100%", height: "100%" }}
                  />
                );
              })()}
            </Box>

            {(stats?.outliers_count ?? 0) > 0 && (
              <Alert
                severity="warning"
                icon={<InfoIcon fontSize="inherit" />}
                sx={{ mt: 6 }}
              >
                <Typography variant="body2">
                  {t("datasets:label.insightOutliers", {
                    count: stats.outliers_count,
                  })}
                </Typography>
              </Alert>
            )}

            {/* Skewness Warning */}
            {(() => {
              const skew = toNumberOrNull(stats?.skew);

              return (
                skew !== null &&
                skew > 1 && (
                  <Alert
                    severity="warning"
                    icon={<InfoIcon fontSize="inherit" />}
                    sx={{ mt: 6 }}
                  >
                    <Typography variant="body2">
                      <Trans i18nKey="datasets:label.rightSkewedWarning">
                        <strong>Right-skewed distribution:</strong> Consider
                        applying a log transformation.
                      </Trans>
                    </Typography>
                  </Alert>
                )
              );
            })()}
          </CardContent>
        </ExportableCard>
      ))}
      {remaining > 0 && (
        <Box display="flex" justifyContent="center" mt={1} mb={2}>
          <Button
            variant="outlined"
            onClick={() => setVisibleCount((c) => c + BATCH_SIZE)}
          >
            {t("datasets:label.showMore", { count: remaining })}
          </Button>
        </Box>
      )}
    </Box>
  );
};
