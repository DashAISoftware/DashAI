import { React, useEffect, useState } from "react";
import { Grid } from "@mui/material";
import Plot from "react-plotly.js";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

import { getExplainerPlot as getExplainerPlotRequest } from "../../api/explainer";

export default function GlobalExplainersPlot({ explainer, scope }) {
  const { enqueueSnackbar } = useSnackbar();
  const [explainerPlot, setExplainerPlot] = useState([]);

  const getExplainerPlot = async () => {
    try {
      const explainerPlot = await getExplainerPlotRequest(explainer.id, scope);
      setExplainerPlot(JSON.parse(explainerPlot));
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the explainers.");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } // finally {
    // setLoading(false);
    // }
  };

  useEffect(() => {
    getExplainerPlot();
  }, []);

  console.log(explainerPlot);

  return (
    <Grid item container flexDirection={"row"} justifyContent={"space-between"}>
      <Grid item xs={8}>
        <Plot
          data={explainerPlot.data}
          layout={{ ...explainerPlot.layout, width: 480, height: 360 }}
          config={{ staticPlot: false }}
        />
      </Grid>
    </Grid>
  );
}

GlobalExplainersPlot.propTypes = {
  explainer: PropTypes.shape({
    explainer_name: PropTypes.string,
    id: PropTypes.number,
    parameters: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string,
        PropTypes.arrayOf(PropTypes.string),
      ]),
    ),
    status: PropTypes.number,
    runId: PropTypes.number,
    explanationPath: PropTypes.string,
    plot_path: PropTypes.string,
    name: PropTypes.string,
    created: PropTypes.string,
  }).isRequired,
  scope: PropTypes.string.isRequired,
};
