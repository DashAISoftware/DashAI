import React from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";

import ResultsGraphsSelection from "./ResultsGraphsSelection";
import ResultsGraphsSwitch from "./ResultsGraphsSwitch";
import ResultsGraphsParameters from "./ResultsGraphsParameters";
import ResultsGraphsPlot from "./ResultsGraphsPlot";

function ResultsGraphsLayout({
  selectedChart,
  handleChangeChart,
  showCustomMetrics,
  handleToggleMetrics,
  tabularMetrics,
  selectedParameters,
  handleToggleParameter,
  selectedGeneralMetric,
  setSelectedGeneralMetric,
  setSelectedParameters,
  concatenatedMetrics,
  chartData,
}) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      textAlign="center"
    >
      {/* Chart selection buttons */}
      <ResultsGraphsSelection
        selectedChart={selectedChart}
        handleChangeChart={handleChangeChart}
      />

      {/* Switch Container */}
      <ResultsGraphsSwitch
        showCustomMetrics={showCustomMetrics}
        handleToggleMetrics={handleToggleMetrics}
      />

      <Box display="flex" justifyContent="flex-start" width="100%">
        {/* Parameter container */}
        <ResultsGraphsParameters
          showCustomMetrics={showCustomMetrics}
          tabularMetrics={tabularMetrics}
          selectedParameters={selectedParameters}
          handleToggleParameter={handleToggleParameter}
          selectedGeneralMetric={selectedGeneralMetric}
          setSelectedGeneralMetric={setSelectedGeneralMetric}
          setSelectedParameters={setSelectedParameters}
          concatenatedMetrics={concatenatedMetrics}
        />

        {/* Plotly Chart */}
        <ResultsGraphsPlot
          selectedChart={selectedChart}
          chartData={chartData}
        />
      </Box>
    </Box>
  );
}

ResultsGraphsLayout.propTypes = {
  selectedChart: PropTypes.string.isRequired,
  handleChangeChart: PropTypes.func.isRequired,
  showCustomMetrics: PropTypes.bool.isRequired,
  handleToggleMetrics: PropTypes.func.isRequired,
  tabularMetrics: PropTypes.array.isRequired,
  selectedParameters: PropTypes.array.isRequired,
  handleToggleParameter: PropTypes.func.isRequired,
  selectedGeneralMetric: PropTypes.string.isRequired,
  setSelectedGeneralMetric: PropTypes.func.isRequired,
  setSelectedParameters: PropTypes.func.isRequired,
  concatenatedMetrics: PropTypes.array.isRequired,
  chartData: PropTypes.object.isRequired,
};

export default ResultsGraphsLayout;
