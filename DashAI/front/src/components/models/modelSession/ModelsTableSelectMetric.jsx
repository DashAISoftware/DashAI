import { MenuItem, TextField } from "@mui/material";
import React, { useEffect, useState } from "react";
import useMetricsByTask from "../../../hooks/useMetricByTask";

function ModelsTableSelectMetric({
  taskName,
  metricName,
  handleSelectedMetric,
  required = false,
  variant = "outlined",
  autoSelectDefault = false,
}) {
  const { compatibleMetrics, loading } = useMetricsByTask({ taskName });
  const [selectedMetric, setSelectedMetric] = useState(metricName);

  // Opt-in only: the run-edit/add-model wizard wants a default goal metric
  // like its other fields (optimizer, its parameters) already have, but the
  // batch-experiment table (ModelsTable.jsx) relies on this field staying
  // empty/required so each row forces an explicit per-row choice — leave
  // that behavior untouched for callers that don't ask for a default.
  useEffect(() => {
    if (
      autoSelectDefault &&
      !selectedMetric &&
      !loading &&
      compatibleMetrics.length > 0
    ) {
      const defaultMetric = compatibleMetrics[0].name;
      setSelectedMetric(defaultMetric);
      handleSelectedMetric(defaultMetric);
    }
  }, [
    autoSelectDefault,
    selectedMetric,
    loading,
    compatibleMetrics,
    handleSelectedMetric,
  ]);

  const handleChange = (e) => {
    const goalMetric = e.target.value;
    setSelectedMetric(goalMetric);
    handleSelectedMetric(goalMetric);
  };

  return (
    <TextField
      select
      value={selectedMetric || ""}
      onChange={handleChange}
      size="small"
      variant={variant}
      fullWidth
      required={required}
      // Without autoSelectDefault, an empty selection is always a real error
      // once loaded (ModelsTable.jsx's batch rows require an explicit
      // per-row choice). With it, a non-empty list with nothing selected yet
      // is only the one render between the list loading and the auto-select
      // effect above filling it in — not a real error — so only a truly
      // empty list (no compatible metric to default to) is worth flagging.
      error={
        required &&
        !selectedMetric &&
        !loading &&
        (!autoSelectDefault || compatibleMetrics.length === 0)
      }
      slotProps={{
        MenuProps: {
          PaperProps: {
            style: {
              maxHeight: 300,
            },
          },
        },
      }}
    >
      {compatibleMetrics.map((metric) => (
        <MenuItem key={metric.name} value={metric.name}>
          {metric.name}
        </MenuItem>
      ))}
    </TextField>
  );
}

export default ModelsTableSelectMetric;
