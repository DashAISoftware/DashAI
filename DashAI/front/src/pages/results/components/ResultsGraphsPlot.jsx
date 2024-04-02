import React from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";
import Plot from "react-plotly.js";

function ResultsGraphsPlot({ selectedChart, chartData }) {
  return (
    <Box>
        <Plot
        data={
            selectedChart === "radar"
            ? chartData.radarValues
            : selectedChart === "bar"
            ? chartData.barValues
            : selectedChart === "pie"
            ? chartData.pieValues
            : []
        }
        layout= {selectedChart === "pie" ? chartData.pieLayout : chartData.generalLayout}
        />
    </Box>
  );
}

ResultsGraphsPlot.propTypes = {
    selectedChart: PropTypes.string.isRequired,
    chartData: PropTypes.object.isRequired,
  };

export default ResultsGraphsPlot;
