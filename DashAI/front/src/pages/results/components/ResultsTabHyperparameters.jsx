import { React, useEffect, useState } from "react";
import PropTypes from "prop-types";
import Plot from "react-plotly.js";
import { FormControl, InputLabel, Grid, MenuItem, Select } from "@mui/material";
import { getHyperparameterPlot as getHyperparameterPlotRequest } from "../../../api/run";
import { enqueueSnackbar } from "notistack";

function ResultsTabHyperparameters({ runData }) {
  const [displayMode, setDisplayMode] = useState("nested-list");
  const [hyperparameterPlots, setHyperparameterPlots] = useState([]);
  function parsePlot(plot) {
    const formattedPlot = JSON.parse(plot);
    const data = formattedPlot.data;
    const layout = formattedPlot.layout;

    // Ejemplo de cómo puedes usar data y layout
    console.log(data); // Mostrará el arreglo de datos
    console.log(layout); // Mostrará el objeto de layout
    return formattedPlot;
  }

  const getHyperparameterPlot = async () => {
    try {
      const hyperparameterPlots = await getHyperparameterPlotRequest(
        runData.id,
      );
      const parsedHyperparameterPlot = parsePlot(hyperparameterPlots);
      setHyperparameterPlots(parsedHyperparameterPlot);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the run data");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Reques error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  useEffect(() => {
    getHyperparameterPlot();
  }, []);
  const { data, layout } = hyperparameterPlots;
  return (
    <Grid container direction="column">
      {console.log("data")}
      {console.log(data)}
      <Plot
        data={data}
        layout={{
          ...layout,
          width: 730,
          height: 380,
        }}
        config={{ staticPlot: false }}
      />
    </Grid>
  );
}

ResultsTabHyperparameters.propTypes = {
  runData: PropTypes.shape({
    parameters: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
        PropTypes.bool,
        PropTypes.object,
      ]),
    ),
  }).isRequired,
};

export default ResultsTabHyperparameters;
