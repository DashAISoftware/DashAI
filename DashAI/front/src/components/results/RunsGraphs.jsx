import { getRuns as getRunsRequest } from "../../api/run";
import PropTypes from "prop-types";
import { getComponents as getComponentsRequest } from "../../api/component";
import { getExperimentById } from "../../api/experiment";
import React, { useEffect, useState } from "react";
import { Button, Box, Switch, Typography, Checkbox, FormControlLabel, Radio, RadioGroup } from "@mui/material";
import Plot from "react-plotly.js";

const runObjectProperties = [
  "train_metrics",
  "test_metrics",
  "validation_metrics",
  "parameters",
];

function RunsGraphs( {experimentId} ) {
  const [selectedChart, setSelectedChart] = useState("radar");
  const [selectedParameters, setSelectedParameters] = useState([]);
  const [chartData, setChartData] = useState({
    generalLayout: null,
    pieLayout: null,
    radarValues: [],
    barValues: [],
    pieValues: [],
  });
  const [showCustomMetrics, setShowCustomMetrics] = useState(false);
  const [selectedGeneralMetric, setSelectedGeneralMetric] = useState("training");

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

  const getRuns = async (experimentId) => {
    try {
      const runs = await getRunsRequest(parseInt(experimentId));
      const experiment = await getExperimentById(parseInt(experimentId));
      return { runs, experiment };
    } catch (error) {
    }
  };

  const tabularGeneralMetrics = ["training", "testing", "validation", "F1", "Accuracy", "Precision", "Recall"];

  const tabularMetrics = ["train Accuracy", "train F1", "train Precision", "train Recall",
                            "test Accuracy", "test F1", "test Precision", "test Recall",
                            "val Accuracy", "val F1", "val Precision", "val Recall"];

  useEffect(() => {
    const processData = async () => {
      const { runs, experiment } = await getRuns(experimentId);
      if (!experiment || experiment.task_name !== "TabularClassificationTask") {
        return null;
      }

      const filteredData = runs.filter(item => item.status === 3);
      const radarValues = [];
      const barValues = [];
      const pieValues = [];
      let parameterIndex = [];
      let generalParameters = [];

      let pieCounter = 0;

      const metricOrder = ['Accuracy', 'F1', 'Precision', 'Recall'];

      if (showCustomMetrics){
        parameterIndex = selectedParameters.map(param => tabularMetrics.indexOf(param));
      }else if (!showCustomMetrics && selectedGeneralMetric.length > 0){
        const criteria = {
          'training': 'train',
          'testing': 'test',
          'validation': 'val',
          'F1': 'F1',
          'Accuracy': 'Accuracy',
          'Precision': 'Precision',
          'Recall': 'Recall'
        };

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

        runObjectProperties.forEach(metricType => {
          if (metricType.endsWith('metrics')) {
            const metrics = item[metricType];
            metricOrder.forEach(metric => {
              numericValues.push(metrics[metric]);
            });
          }
        });

        const relevantNumericValues = parameterIndex.map(index => numericValues[index]);

        radarValues.push({
          type: "scatterpolar",
          r: relevantNumericValues,
          theta: showCustomMetrics ? selectedParameters : generalParameters,
          fill: "toself",
          name: item.name,
          automargin: true
        });

        barValues.push({
          x: showCustomMetrics ? selectedParameters : generalParameters,
          y: relevantNumericValues,
          type: 'bar',
          name: item.name,
          automargin: true
        });

        pieValues.push({
          labels: showCustomMetrics ? selectedParameters : generalParameters,
          values: relevantNumericValues,
          type: 'pie',
          name: item.name,
          domain: {
            row: Math.floor(pieCounter / 2),
            column: pieCounter % 2
          },
          hoverinfo: 'label+percent+name',
          textinfo: 'percent',
          textposition: 'inside',
          automargin: true,
          title: item.name
        });

        pieCounter+= 1;
      });

      const generalLayout = {
        polar: { radialaxis: { visible: selectedChart === "radar", range: [0, 1] } },
        showlegend: true,
        width: 600,
        height: 400,
      };

      let numRows, numColumns;
      if (pieValues.length <= 2) {
        numRows = 1;
        numColumns = pieValues.length;
      } else {
        numRows = Math.ceil(pieValues.length / 2);
        numColumns = Math.min(2, pieValues.length);
      }

      const pieLayout = {
        height: 400,
        width: 600,
        grid: {rows: numRows, columns: numColumns},
        legend: {
          itemclick: false
        }
      };
      setChartData({ generalLayout, pieLayout, radarValues, barValues, pieValues });
    };
    processData();
  }, [selectedParameters, selectedChart]);

  return (
    <>
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
  <Box mb={2} display="flex" justifyContent="center" width="100%">
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

  <Box display="flex" flexDirection="row" alignItems="center" justifyContent="center">
    {/* Parameter container */}
    <Box
      bgcolor="#2F2F2F"
      p={2}
      mr={1}
      display="flex"
      flexDirection="column"
      alignItems="flex-start"
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
          {tabularGeneralMetrics.map((param) => (
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
