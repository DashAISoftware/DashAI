import React, { useState } from "react";
import {
  Grid,
  TextField,
  Select,
  FormControl,
  InputLabel,
  MenuItem,
} from "@mui/material";
import Plot from "react-plotly.js";
import PropTypes from "prop-types";

/**
 * PartialDependencePlot function to generate data for the plot
 * @param {*} explanation explanation to plot
 * @returns data to plot, layout and actions modal
 */
function PartialDependencePlot(explanation) {
  const features = Object.keys(explanation);
  const [currentFeature, setCurrentFeature] = useState(0);
  const [currentClass, setCurrentClass] = useState(0);

  const data = [
    {
      x: explanation[features[currentFeature]].grid_values,
      y: explanation[features[currentFeature]].average[currentClass],
      type: "scatter",
      mode: "lines",
    },
  ];

  const layout = {
    title: "Partial Dependence Plot",
  };

  function plotActions() {
    return (
      <Grid container display={"flex"} flexDirection={"column"} rowGap={2}>
        <Grid item>
          <FormControl variant="outlined" sx={{ minWidth: "200px" }}>
            <InputLabel id="select-type-label">class</InputLabel>
            <Select
              id="select-type"
              value={currentClass}
              onChange={(event) => setCurrentClass(event.target.value)}
              label="class"
              autoWidth
            >
              {Object.keys(explanation[features[currentFeature]].average).map(
                (_, i) => (
                  <MenuItem key={i} value={i}>
                    class {i}
                  </MenuItem>
                ),
              )}
            </Select>
          </FormControl>
        </Grid>
        <Grid item>
          <FormControl variant="outlined" sx={{ minWidth: "200px" }}>
            <InputLabel id="select-type-label">feature</InputLabel>
            <Select
              id="select-type"
              value={currentFeature}
              onChange={(event) => {
                setCurrentFeature(event.target.value);
                setCurrentClass(0);
              }}
              label="class"
              autoWidth
            >
              {features.map((feat, i) => (
                <MenuItem key={i} value={i}>
                  {feat}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    );
  }
  return { data, layout, plotActions };
}

/**
 * PermutationFeatureImportancePlot function to generate data for the plot
 * @param {*} explanation explanation to plot
 * @returns data to plot, layout and actions modal
 */
function PermutationFeatureImportancePlot(explanation) {
  const [currentFeaturesNumber, setCurrentFeaturesNumber] = useState(
    explanation.features.length,
  );

  const data = [
    {
      x: explanation.importances_mean.slice(0, currentFeaturesNumber),
      y: explanation.features.slice(0, currentFeaturesNumber),
      type: "bar",
      orientation: "h",
    },
  ];

  const layout = {
    title: "Permutation Feature Importance Plot",
  };

  function plotActions() {
    return (
      <Grid container display={"flex"} flexDirection={"column"} rowGap={2}>
        <Grid item>
          <TextField
            id="number-of-features"
            label="number of features"
            value={currentFeaturesNumber}
            onChange={(event) => {
              setCurrentFeaturesNumber(event.target.value);
            }}
            type="number"
            InputProps={{
              inputProps: {
                min: 1,
                max: explanation.features.length,
                style: { textAlign: "center" },
              },
            }}
            sx={{ minWidth: "200px" }}
          />
        </Grid>
      </Grid>
    );
  }
  return { data, layout, plotActions };
}

/**
 * GlobalExplainersPlot
 * @param {*} explainerType
 * @returns Component that renders the explanation plot and actions
 */
export default function GlobalExplainersPlot({ explainerType }) {
  // here explanations should be obtained from the back

  // explanation example for Partial Dependance
  const explanation1 = {
    battery_power: {
      grid_values: [
        504.0, 669.56, 835.11, 1000.67, 1166.22, 1331.78, 1497.33, 1662.89,
        1828.44, 1994.0,
      ],
      average: [
        [0.31, 0.31, 0.3, 0.29, 0.28, 0.23, 0.22, 0.21, 0.19, 0.18],
        [0.26, 0.25, 0.25, 0.25, 0.26, 0.27, 0.25, 0.25, 0.25, 0.26],
        [0.26, 0.26, 0.25, 0.25, 0.24, 0.23, 0.24, 0.25, 0.26, 0.26],
        [0.17, 0.18, 0.19, 0.2, 0.22, 0.27, 0.29, 0.29, 0.3, 0.3],
      ],
    },
    blue: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.24],
        [0.25, 0.25],
      ],
    },
    clock_speed: {
      grid_values: [0.5, 0.78, 1.06, 1.33, 1.61, 1.89, 2.17, 2.44, 2.72, 3.0],
      average: [
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26],
        [0.25, 0.26, 0.26, 0.26, 0.26, 0.26, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24],
      ],
    },
    dual_sim: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.26],
        [0.25, 0.25],
        [0.25, 0.25],
      ],
    },
    fc: {
      grid_values: [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0],
      average: [
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24],
        [0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26],
        [0.24, 0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26],
        [0.25, 0.25, 0.25, 0.24, 0.24, 0.24, 0.24, 0.24, 0.24, 0.24],
      ],
    },
    four_g: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.26],
        [0.25, 0.24],
        [0.25, 0.25],
      ],
    },
    int_memory: {
      grid_values: [
        2.0, 8.89, 15.78, 22.67, 29.56, 36.44, 43.33, 50.22, 57.11, 64.0,
      ],
      average: [
        [0.25, 0.26, 0.26, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.23],
        [0.26, 0.25, 0.25, 0.25, 0.26, 0.26, 0.25, 0.25, 0.25, 0.28],
        [0.27, 0.26, 0.25, 0.25, 0.24, 0.24, 0.24, 0.24, 0.24, 0.23],
        [0.23, 0.24, 0.24, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26, 0.26],
      ],
    },
    m_dep: {
      grid_values: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
      average: [
        [0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26, 0.27],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24],
      ],
    },
    mobile_wt: {
      grid_values: [
        80.0, 93.33, 106.67, 120.0, 133.33, 146.67, 160.0, 173.33, 186.67,
        200.0,
      ],
      average: [
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.26, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.22, 0.23, 0.24, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.25],
        [0.27, 0.27, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24, 0.23, 0.24],
      ],
    },
    n_cores: {
      grid_values: [1, 2, 3, 4, 5, 6, 7, 8],
      average: [
        [0.24, 0.25, 0.25, 0.25, 0.26, 0.26, 0.26, 0.25],
        [0.29, 0.26, 0.26, 0.25, 0.24, 0.24, 0.24, 0.24],
        [0.22, 0.24, 0.24, 0.25, 0.25, 0.25, 0.25, 0.26],
        [0.25, 0.24, 0.24, 0.25, 0.25, 0.25, 0.25, 0.25],
      ],
    },
    pc: {
      grid_values: [
        0.0, 2.22, 4.44, 6.67, 8.89, 11.11, 13.33, 15.56, 17.78, 20.0,
      ],
      average: [
        [0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.27],
        [0.25, 0.25, 0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24],
        [0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24],
      ],
    },
    px_height: {
      grid_values: [
        13.0, 228.11, 443.22, 658.33, 873.44, 1088.56, 1303.67, 1518.78,
        1733.89, 1949.0,
      ],
      average: [
        [0.28, 0.27, 0.27, 0.25, 0.24, 0.23, 0.21, 0.19, 0.18, 0.17],
        [0.26, 0.25, 0.26, 0.26, 0.26, 0.26, 0.25, 0.25, 0.26, 0.25],
        [0.26, 0.25, 0.24, 0.24, 0.24, 0.24, 0.25, 0.25, 0.25, 0.28],
        [0.21, 0.23, 0.24, 0.25, 0.26, 0.28, 0.29, 0.3, 0.32, 0.3],
      ],
    },
    px_width: {
      grid_values: [
        503.0, 668.78, 834.56, 1000.33, 1166.11, 1331.89, 1497.67, 1663.44,
        1829.22, 1995.0,
      ],
      average: [
        [0.3, 0.27, 0.26, 0.26, 0.26, 0.26, 0.25, 0.23, 0.21, 0.2],
        [0.25, 0.26, 0.26, 0.26, 0.26, 0.25, 0.25, 0.24, 0.26, 0.27],
        [0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.23, 0.23],
        [0.21, 0.22, 0.22, 0.23, 0.23, 0.25, 0.25, 0.28, 0.3, 0.3],
      ],
    },
    ram: {
      grid_values: [
        258.0, 672.78, 1087.56, 1502.33, 1917.11, 2331.89, 2746.67, 3161.44,
        3576.22, 3991.0,
      ],
      average: [
        [0.73, 0.72, 0.57, 0.24, 0.12, 0.06, 0.04, 0.03, 0.03, 0.03],
        [0.18, 0.2, 0.32, 0.53, 0.53, 0.3, 0.14, 0.09, 0.08, 0.07],
        [0.06, 0.06, 0.08, 0.18, 0.28, 0.48, 0.53, 0.33, 0.23, 0.2],
        [0.03, 0.03, 0.03, 0.05, 0.07, 0.16, 0.29, 0.55, 0.67, 0.69],
      ],
    },
    sc_h: {
      grid_values: [
        5.0, 6.56, 8.11, 9.67, 11.22, 12.78, 14.33, 15.89, 17.44, 19.0,
      ],
      average: [
        [0.25, 0.25, 0.25, 0.26, 0.26, 0.26, 0.26, 0.25, 0.25, 0.26],
        [0.26, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24, 0.24, 0.24, 0.25],
        [0.24, 0.24, 0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24],
      ],
    },
    sc_w: {
      grid_values: [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0],
      average: [
        [0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.25, 0.25, 0.24, 0.24],
        [0.25, 0.26, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.24, 0.24],
        [0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26],
        [0.25, 0.25, 0.25, 0.24, 0.24, 0.25, 0.25, 0.25, 0.26, 0.25],
      ],
    },
    talk_time: {
      grid_values: [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
      average: [
        [0.25, 0.26, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
        [0.26, 0.25, 0.25, 0.25, 0.25, 0.26, 0.26, 0.25, 0.26, 0.26],
        [0.25, 0.25, 0.25, 0.24, 0.24, 0.24, 0.25, 0.25, 0.25, 0.24],
        [0.24, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
      ],
    },
    three_g: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.25],
      ],
    },
    touch_screen: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.25],
        [0.25, 0.25],
      ],
    },
    wifi: {
      grid_values: [0, 1],
      average: [
        [0.25, 0.25],
        [0.25, 0.26],
        [0.25, 0.25],
        [0.25, 0.25],
      ],
    },
  };

  // explanation example for PermutationFeatureImportance
  const explanation4 = {
    features: [
      "ram",
      "wifi",
      "touch_screen",
      "three_g",
      "talk_time",
      "sc_w",
      "sc_h",
      "px_width",
      "px_height",
      "pc",
      "n_cores",
      "mobile_wt",
      "m_dep",
      "int_memory",
      "four_g",
      "fc",
      "dual_sim",
      "clock_speed",
      "blue",
      "battery_power",
    ],
    importances_mean: [
      0.56, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14,
      -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14, -0.14,
    ],
  };

  /**
   * ExplainerRender function to switch between explainer types and call the right function to generate the plot data
   * @returns data to plot, layout and actions modal
   */
  function ExplainerRender() {
    switch (explainerType) {
      // should recieve a single generated explanation from the back, but for now uses the examples.
      case "PartialDependence":
        return PartialDependencePlot(explanation1);
      case "PermutationFeatureImportance":
        return PermutationFeatureImportancePlot(explanation4);
      default:
        return { data: [], plotActions: () => <></> };
    }
  }

  const { data, layout, plotActions } = ExplainerRender();

  return (
    <Grid item container flexDirection={"row"} justifyContent={"space-between"}>
      <Grid item xs={4}>
        {plotActions()}
      </Grid>
      <Grid item xs={8}>
        <Plot
          data={data}
          layout={{ ...layout, width: 480, height: 360 }}
          config={{ staticPlot: true }}
        />
      </Grid>
    </Grid>
  );
}

GlobalExplainersPlot.propTypes = {
  explainerType: PropTypes.string.isRequired,
};
