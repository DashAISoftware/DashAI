import { getRuns as getRunsRequest } from "../../../api/run";
import PropTypes from "prop-types";
import { getExperimentById } from "../../../api/experiment";
import React, { useEffect, useState } from "react";
import { Alert, AlertTitle } from "@mui/material";
import { useSnackbar } from "notistack";
import graphsMaking from "../constants/graphsMaking";
import layoutMaking from "../constants/layoutMaking";

import ResultsGraphsLayout from "./ResultsGraphsLayout";

function ResultsGraphs({ experimentId }) {
  const { enqueueSnackbar } = useSnackbar();
  const [selectedChart, setSelectedChart] = useState("radar");
  const [selectedParameters, setSelectedParameters] = useState([]);
  const [showCustomMetrics, setShowCustomMetrics] = useState(false);
  const [selectedGeneralMetric, setSelectedGeneralMetric] = useState("test");
  const [concatenatedMetrics, setConcatenatedMetrics] = useState([]);
  const [tabularMetrics, setTabularMetrics] = useState([]);
  const [chartData, setChartData] = useState({});
  const [filteredDataProcess, setFilteredDataProcess] = useState([]);

  const handleChangeChart = (chartType) => {
    setSelectedChart(chartType);
  };

  const handleToggleParameter = (parameter) => {
    const updatedParameters = selectedParameters.includes(parameter)
      ? selectedParameters.filter((param) => param !== parameter)
      : [...selectedParameters, parameter];
    setSelectedParameters(updatedParameters);
  };

  const handleToggleMetrics = () => {
    setShowCustomMetrics(!showCustomMetrics);
    setSelectedParameters([]);
  };

  const getRuns = async () => {
    try {
      const runs = await getRunsRequest(parseInt(experimentId));
      const experiment = await getExperimentById(parseInt(experimentId));
      return { runs, experiment };
    } catch (error) {
      enqueueSnackbar(
        `Error while trying to obtain data of the experiment id: ${experimentId}`,
      );
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  useEffect(() => {
    const processData = async () => {
      const { runs } = await getRuns(experimentId);

      // Only process the data with status Finished
      const filteredData = runs.filter((item) => item.status === 3);
      setFilteredDataProcess(filteredData);
      const graphsToView = {};
      let parameterIndex = [];
      const generalParameters = [];
      let pieCounter = 0;

      // Filter all metrics with status Finished and obtain all the keywords metrics
      const newFilteredDataWithMetrics = filteredData.map((item) => {
        const metrics = {};
        Object.keys(item).forEach((key) => {
          if (key.includes("metrics")) {
            metrics[key] = item[key];
          }
        });
        return metrics;
      });

      if (newFilteredDataWithMetrics.length > 0) {
        // Order in which metrics appear
        const metricsOrder = Object.keys(newFilteredDataWithMetrics[0]);
        const metricsValuesOrder = Object.keys(
          newFilteredDataWithMetrics[0][metricsOrder[0]],
        );
        const concatenatedMetrics = metricsOrder
          .map((metricType) => metricType.split("_")[0])
          .concat(metricsValuesOrder);
        setConcatenatedMetrics(concatenatedMetrics);

        const tabularMetrics = [];
        metricsOrder.forEach((metricType) => {
          metricsValuesOrder.forEach((metric) => {
            tabularMetrics.push(`${metricType.split("_")[0]} ${metric}`);
          });
        });

        if (showCustomMetrics) {
          parameterIndex = selectedParameters.map((param) =>
            tabularMetrics.indexOf(param),
          );
        } else if (!showCustomMetrics && selectedGeneralMetric.length > 0) {
          setTabularMetrics(tabularMetrics);
          const criteria = {};
          concatenatedMetrics.forEach((item) => {
            criteria[item] = item;
          });

          tabularMetrics.forEach((metric, index) => {
            Object.entries(criteria).forEach(([metricName, substring]) => {
              if (
                selectedGeneralMetric === metricName &&
                metric.includes(substring)
              ) {
                parameterIndex.push(index);
                generalParameters.push(metric);
              }
            });
          });
        } else {
          parameterIndex = [];
        }

        filteredData.forEach((item) => {
          const numericValues = [];

          metricsOrder.forEach((metricType) => {
            if (metricType.endsWith("metrics")) {
              const metrics = item[metricType];
              metricsValuesOrder.forEach((metric) => {
                numericValues.push(metrics[metric]);
              });
            }
          });

          const relevantNumericValues = parameterIndex.map(
            (index) => numericValues[index],
          );
          graphsMaking(
            graphsToView,
            item,
            relevantNumericValues,
            showCustomMetrics,
            selectedParameters,
            generalParameters,
            pieCounter,
          );
          pieCounter += 1;
        });

        // Call the Layouts to use
        const { generalLayout, pieLayout } = layoutMaking(
          selectedChart,
          graphsToView,
        );

        // Call the Graphs to use, make sure to see the correct order in RunsGraphsLayout.jsx
        const graphsToViewKeys = Object.keys(graphsToView);
        const radarValues = graphsToView[graphsToViewKeys[0]];
        const barValues = graphsToView[graphsToViewKeys[1]];
        const pieValues = graphsToView[graphsToViewKeys[2]];

        setChartData({
          generalLayout,
          pieLayout,
          radarValues,
          barValues,
          pieValues,
        });
      }
    };
    processData();
  }, [selectedParameters, selectedChart]);

  return (
    <>
      {filteredDataProcess.length === 0 ? (
        <>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <AlertTitle>No information from the experiments</AlertTitle>
            There are no completed experiments or all have an error status.
          </Alert>
        </>
      ) : (
        <ResultsGraphsLayout
          selectedChart={selectedChart}
          handleChangeChart={handleChangeChart}
          showCustomMetrics={showCustomMetrics}
          handleToggleMetrics={handleToggleMetrics}
          tabularMetrics={tabularMetrics}
          selectedParameters={selectedParameters}
          handleToggleParameter={handleToggleParameter}
          selectedGeneralMetric={selectedGeneralMetric}
          setSelectedGeneralMetric={setSelectedGeneralMetric}
          setSelectedParameters={setSelectedParameters}
          concatenatedMetrics={concatenatedMetrics}
          chartData={chartData}
        />
      )}
    </>
  );
}

ResultsGraphs.propTypes = {
  experimentId: PropTypes.string,
};

ResultsGraphs.defaultProps = {
  experimentId: undefined,
};

export default ResultsGraphs;
