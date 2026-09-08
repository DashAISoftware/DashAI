import { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { getOuterAveragedMetrics } from "../../api/run";

const fmt = (mean, std) => {
  if (mean == null) return "—";
  const m = mean.toFixed(4);
  return std != null ? `${m} ± ${std.toFixed(4)}` : m;
};

/**
 * Table with the averaged metrics across the outer folds of a nested-CV run
 */
export default function OuterFoldMetricsTable({ run }) {
  const { t } = useTranslation("models");
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!run.id) return;

    const controller = new AbortController();
    setLoading(true);
    setError(false);

    const fetchAveraged = async () => {
      try {
        const data = await getOuterAveragedMetrics(run.id, {
          signal: controller.signal,
        });
        setMetrics(data);
      } catch (err) {
        if (err.name === "CanceledError" || err.name === "AbortError") return;
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchAveraged();

    return () => controller.abort();
  }, [run.id]);

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const train = metrics?.train_metrics || {};
  // Nested CV scores each outer fold on its validation partition.
  const validation = metrics?.validation_metrics || {};
  const trainStd = metrics?.train_metrics_std || {};
  const validationStd = metrics?.validation_metrics_std || {};

  const metricNames = Array.from(
    new Set([...Object.keys(train), ...Object.keys(validation)]),
  ).sort();

  if (error || metricNames.length === 0) {
    return (
      <Alert severity="info" sx={{ m: 1.5 }}>
        {t("models:message.noOuterMetrics")}
      </Alert>
    );
  }

  return (
    <Box sx={{ flex: 1, minHeight: 0, overflow: "auto", px: 1.5, pb: 1.5 }}>
      <TableContainer>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>
                {t("models:label.metric")}
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>
                {t("models:label.train")}
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 600 }}>
                {t("models:label.validation")}
              </TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {metricNames.map((name) => (
              <TableRow key={name} hover>
                <TableCell>{name}</TableCell>
                <TableCell align="right">
                  {fmt(train[name], trainStd[name])}
                </TableCell>
                <TableCell align="right">
                  {fmt(validation[name], validationStd[name])}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

OuterFoldMetricsTable.propTypes = {
  runId: PropTypes.number,
};
