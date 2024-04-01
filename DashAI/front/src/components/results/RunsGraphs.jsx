import { getRuns as getRunsRequest } from "../../api/run";
import PropTypes from "prop-types";
import { getExperimentById } from "../../api/experiment";
import React, { useEffect, useState } from "react";
import { Alert, AlertTitle, Button, Box, Switch, Typography, Checkbox, FormControlLabel, Radio, RadioGroup } from "@mui/material";
import Plot from "react-plotly.js";
import graphsMaking from "./RunsGraphsMaking";
import layoutMaking from "./RunsGraphsLayout";

function RunsGraphs( {experimentId} ) {
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
    }
  };

  useEffect(() => {
    const processData = async () => {
      const { runs, experiment } = await getRuns(experimentId);

      // Only process the data with status Finished
      const filteredData = runs.filter(item => item.status === 3);
      setFilteredDataProcess(filteredData);
      const graphsToView = {};
      let parameterIndex = [];
      let generalParameters = [];
      let pieCounter = 0;

      // Filter all metrics with status Finished and obtain all the keywords metrics
      const newFilteredDataWithMetrics = filteredData
        .map(item => {
          const metrics = {};
          Object.keys(item).forEach(key => {
            if (key.includes('metrics')) {
              metrics[key] = item[key];
            }
          });
          return metrics;
        });
      
      // Order in which metrics appear
      const metricsOrder = Object.keys(newFilteredDataWithMetrics[0]);
      const metricsValuesOrder = Object.keys(newFilteredDataWithMetrics[0][metricsOrder[0]]);
      const concatenatedMetrics = metricsOrder.map(metricType => metricType.split('_')[0]).concat(metricsValuesOrder);
      setConcatenatedMetrics(concatenatedMetrics);

      const tabularMetrics = [];
      metricsOrder.forEach(metricType => {
        metricsValuesOrder.forEach(metric => {
          tabularMetrics.push(`${metricType.split('_')[0]} ${metric}`);
        });
      });
  
      if (showCustomMetrics){
        parameterIndex = selectedParameters.map(param => tabularMetrics.indexOf(param));
      }else if (!showCustomMetrics && selectedGeneralMetric.length > 0){
        setTabularMetrics(tabularMetrics);
        const criteria = {};
        concatenatedMetrics.forEach(item => {
          criteria[item] = item;
        });

        tabularMetrics.forEach((metric, index) => {
          Object.entries(criteria).forEach(([metricName, substring]) => {
            if (selectedGeneralMetric === metricName && metric.includes(substring)) {
              parameterIndex.push(index);
              generalParameters.push(metric);
            }
          });
        });
      } else {
        parameterIndex = [];
      }

      filteredData.forEach(item => {
        const numericValues = [];

        metricsOrder.forEach(metricType => {
          if (metricType.endsWith('metrics')) {
            const metrics = item[metricType];
            metricsValuesOrder.forEach(metric => {
              numericValues.push(metrics[metric]);
            });
          }
        });

        const relevantNumericValues = parameterIndex.map(index => numericValues[index]);
        graphsMaking(graphsToView, item, relevantNumericValues, showCustomMetrics, selectedParameters, generalParameters, pieCounter);
        pieCounter+= 1;
      });

      // Call the Layouts to use
      let {generalLayout, pieLayout} = layoutMaking(selectedChart, graphsToView)

      // Call the Graphs to use, make sure to see the correct order in RunsGraphsLayout.jsx
      const graphsToViewKeys = Object.keys(graphsToView);
      let radarValues = graphsToView[graphsToViewKeys[0]];
      let barValues = graphsToView[graphsToViewKeys[1]];
      let pieValues = graphsToView[graphsToViewKeys[2]];

      setChartData({ generalLayout, pieLayout, radarValues, barValues, pieValues });
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
        <Box display="flex" flexDirection="column" alignItems="center" textAlign="center">
          {/* Chart selection buttons */}
          <Box p={2} mb={2}>
            <Button
              variant="text"
              color={selectedChart === "radar" ? "primary" : "inherit"}
              onClick={() => handleChangeChart("radar")}
              style={{ borderBottom: selectedChart === "radar" ? "2px solid #00bebb" : "2px solid #ffffff", marginRight: "30px", marginTop: "-15px" }}
            >
              Radar
            </Button>
            <Button
              variant="text"
              color={selectedChart === "bar" ? "primary" : "inherit"}
              onClick={() => handleChangeChart("bar")}
              style={{ borderBottom: selectedChart === "bar" ? "2px solid #00bebb" : "2px solid #ffffff", marginTop: "-15px" }}
            >
              Bar
            </Button>
            <Button
              variant="text"
              color={selectedChart === "pie" ? "primary" : "inherit"}
              onClick={() => handleChangeChart("pie")}
              style={{ borderBottom: selectedChart === "pie" ? "2px solid #00bebb" : "2px solid #ffffff", marginLeft: "30px", marginTop: "-15px" }}
            >
              Pie
            </Button>
          </Box>
          
          {/* Switch Container */}
          <Box mb={2} display="flex" justifyContent="flex-start" width="100%">
            <Box display="flex" alignItems="center">
              <Typography variant="subtitle2" style={{ fontSize: "0.8rem" }}>General metrics</Typography>
            </Box>
            <Box display="flex" alignItems="center">
              <Switch
                checked={showCustomMetrics}
                onChange={handleToggleMetrics}
                color="primary"
                name="metricsSwitch"
                inputProps={{ 'aria-label': 'Cambiar métricas' }}
              />
            </Box>
            <Box display="flex" alignItems="center">
              <Typography variant="subtitle2" style={{ fontSize: "0.8rem" }}>Custom metrics</Typography>
            </Box>
          </Box>

          <Box display="flex" justifyContent="flex-start" width="100%">
            {/* Parameter container */}
            <Box
              bgcolor="#2F2F2F"
              p={2}
              mr={1}
              display="flex"
              flexDirection="column"
              alignItems="flex-start"
              width="250px"
              sx={{
                "& .MuiCheckbox-root": {
                  padding: "3px 0",
                },
                "& .MuiTypography-root": {
                  padding: "3px 0",
                },
              }}
            >
              {showCustomMetrics
                ? tabularMetrics.map((param) => (
                    <FormControlLabel
                      key={param}
                      control={<Checkbox checked={selectedParameters.includes(param)} onChange={() => handleToggleParameter(param)} />}
                      label={param}
                    />
                  ))
                : (
                <RadioGroup 
                  value={selectedGeneralMetric} 
                  onChange={(event) => {
                    const selectedMetric = event.target.value;
                    setSelectedGeneralMetric(selectedMetric);
                    setSelectedParameters([selectedMetric]);
                  }}
                >
                  {concatenatedMetrics.map((param) => (
                    <FormControlLabel
                      key={param}
                      value={param}
                      control={<Radio checked={selectedGeneralMetric === param} />}
                      label={param}
                    />
                  ))}
                </RadioGroup>
                )
                  }   
            </Box>

            {/* Plotly Chart */}
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
          </Box>
        </Box>
      )}
    </>
  );
}

RunsGraphs.propTypes = {
    experimentId: PropTypes.string,
};
  
RunsGraphs.defaultProps = {
    experimentId: undefined,
};

export default RunsGraphs;
