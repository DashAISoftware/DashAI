import React from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";

import ResultsGraphsParameters from "./ResultsGraphsParameters";
import ResultsGraphsPlot from "./ResultsGraphsPlot";

function ResultsGraphsLayout({
  currentMetrics,
  selectedMetrics,
  handleToggleMetric,
  handleSelectAll,
  handleClearAll,
  chartData,
  onToggleRun,
  sessionId,
}) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="stretch"
      width="100%"
      height="100%"
    >
      {/* Metric filter toolbar */}
      <Box sx={{ display: "flex", justifyContent: "flex-start", px: 4, py: 3 }}>
        <ResultsGraphsParameters
          currentMetrics={currentMetrics}
          selectedMetrics={selectedMetrics}
          handleToggleMetric={handleToggleMetric}
          handleSelectAll={handleSelectAll}
          handleClearAll={handleClearAll}
        />
      </Box>

      {/* Plotly chart area — bar panels + heatmap in one grid */}
      <Box display="flex" flex={1} width="100%">
        {/* Remounts (resetting the drag-order state cleanly) whenever the
            session changes instead of reusing the instance across sessions */}
        <ResultsGraphsPlot
          key={sessionId}
          chartData={chartData}
          onToggleRun={onToggleRun}
          sessionId={sessionId}
        />
      </Box>
    </Box>
  );
}

ResultsGraphsLayout.propTypes = {
  currentMetrics: PropTypes.array.isRequired,
  selectedMetrics: PropTypes.array.isRequired,
  handleToggleMetric: PropTypes.func.isRequired,
  handleSelectAll: PropTypes.func.isRequired,
  handleClearAll: PropTypes.func.isRequired,
  chartData: PropTypes.object.isRequired,
  onToggleRun: PropTypes.func.isRequired,
  sessionId: PropTypes.number,
};

export default ResultsGraphsLayout;
