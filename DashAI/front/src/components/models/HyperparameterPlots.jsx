import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { CircularProgress, Box, Typography } from "@mui/material";
import { getHyperparameterPlot as getHyperparameterPlotRequest } from "../../api/run";
import { enqueueSnackbar } from "notistack";
import { checkHowManyOptimazers } from "../../utils/schema";
import ArtifactViewer from "../shared/ArtifactViewer";

function HyperparameterPlots({ run }) {
  // Each plot now arrives as a typed artifact ({type, payload, title}) built
  // server side, same contract Explainers/Explorers use - no client side
  // parsing or title guessing needed.
  const [historicalPlot, setHistoricalPlot] = useState(null);
  const [slicePlot, setSlicePlot] = useState(null);
  const [contourPlot, setContourPlot] = useState(null);
  const [importancePlot, setImportancePlot] = useState(null);
  const [loading, setLoading] = useState(true);

  const optimizables = checkHowManyOptimazers({
    params: run.parameters,
  });

  const getHyperparameterPlot = async () => {
    try {
      setLoading(true);
      if (optimizables >= 2) {
        const [historical, slice, contour, importance] = await Promise.all([
          getHyperparameterPlotRequest(run.id, 1),
          getHyperparameterPlotRequest(run.id, 2),
          getHyperparameterPlotRequest(run.id, 3),
          getHyperparameterPlotRequest(run.id, 4),
        ]);

        setHistoricalPlot(historical);
        setSlicePlot(slice);
        setContourPlot(contour);
        setImportancePlot(importance);
      } else if (optimizables === 1) {
        const [historical, slice] = await Promise.all([
          getHyperparameterPlotRequest(run.id, 1),
          getHyperparameterPlotRequest(run.id, 2),
        ]);

        setHistoricalPlot(historical);
        setSlicePlot(slice);
      }
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain hyperparameter plots", {
        variant: "error",
      });
      console.error("Error loading hyperparameter plots:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (run.status === 3) {
      getHyperparameterPlot();
    } else {
      setLoading(false);
    }
  }, [run.id, run.status, run.parameters]);

  if (loading) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 400,
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (run.status === 2 || run.status === 1) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 400,
        }}
      >
        <Typography color="textSecondary">
          Training in progress. Hyperparameter plots will be available when
          training completes.
        </Typography>
      </Box>
    );
  }

  if (run.status === 4) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 400,
        }}
      >
        <Typography color="error">
          Run failed. No hyperparameter plots available.
        </Typography>
      </Box>
    );
  }

  if (run.status === 0) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 400,
        }}
      >
        <Typography color="textSecondary">
          Run not started. No hyperparameter plots available.
        </Typography>
      </Box>
    );
  }

  if (!historicalPlot && !slicePlot) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: 400,
        }}
      >
        <Typography color="textSecondary">
          No hyperparameter plots available.
        </Typography>
      </Box>
    );
  }

  const artifacts = [
    historicalPlot,
    slicePlot,
    optimizables >= 2 && contourPlot,
    optimizables >= 2 && importancePlot,
  ].filter(Boolean);

  return (
    <Box sx={{ p: 4 }}>
      <Box
        sx={{
          display: "grid",
          gap: 4,
          // Wider floor than Live Metrics' panels (420px) - these plots carry
          // more horizontal detail (legend, colorbar, wide trial axis) and
          // look sparse/oversized stretched full width on a wide screen, but
          // still don't need a whole row to themselves once there's room for
          // a second column.
          gridTemplateColumns: "repeat(auto-fit, minmax(600px, 1fr))",
        }}
      >
        {artifacts.map((artifact, index) => (
          <ArtifactViewer
            key={artifact.index ?? index}
            artifact={artifact}
            siblingArtifacts={artifacts}
            siblingIndex={index}
          />
        ))}
      </Box>
    </Box>
  );
}

HyperparameterPlots.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number.isRequired,
    status: PropTypes.number.isRequired,
    parameters: PropTypes.object.isRequired,
  }).isRequired,
};

export default HyperparameterPlots;
