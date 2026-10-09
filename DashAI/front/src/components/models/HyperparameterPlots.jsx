import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { CircularProgress, Box, Typography } from "@mui/material";
import { getHyperparameterPlot as getHyperparameterPlotRequest } from "../../api/run";
import { enqueueSnackbar } from "notistack";
import { checkHowManyOptimazers } from "../../utils/schema";
import ArtifactViewer from "../shared/ArtifactViewer";

const PLOT_TYPES = { history: 1, slice: 2, contour: 3, importance: 4 };

function HyperparameterPlots({ run }) {
  // Each plot now arrives as a typed artifact ({type, payload, title}) built
  // server side, same contract Explainers/Explorers use - no client side
  // parsing or title guessing needed.
  const [plots, setPlots] = useState([]);
  const [loading, setLoading] = useState(true);

  const optimizables = checkHowManyOptimazers({
    params: run.parameters,
  });

  const getHyperparameterPlot = async () => {
    const wanted =
      optimizables >= 2
        ? [
            PLOT_TYPES.history,
            PLOT_TYPES.slice,
            PLOT_TYPES.contour,
            PLOT_TYPES.importance,
          ]
        : optimizables === 1
          ? [PLOT_TYPES.history, PLOT_TYPES.slice]
          : [];

    setLoading(true);
    const settled = await Promise.allSettled(
      wanted.map((plotType) => getHyperparameterPlotRequest(run.id, plotType)),
    );

    const available = [];
    const failures = [];
    settled.forEach((result, i) => {
      if (result.status === "fulfilled") {
        if (result.value) {
          available.push({ plotType: wanted[i], artifact: result.value });
        }
      } else if (result.reason?.response?.status !== 404) {
        failures.push(result.reason);
      }
    });

    setPlots(available);
    setLoading(false);

    if (failures.length > 0) {
      enqueueSnackbar("Error while trying to obtain hyperparameter plots", {
        variant: "error",
      });
      console.error("Error loading hyperparameter plots:", failures);
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

  if (plots.length === 0) {
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

  const artifacts = plots.map(({ artifact }) => artifact);

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
        {plots.map(({ plotType, artifact }, index) => (
          <ArtifactViewer
            key={plotType}
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
