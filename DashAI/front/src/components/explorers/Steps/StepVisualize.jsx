import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import { useExplorerContext } from "../context";
import { Box } from "@mui/material";

function StepVisualize({}) {
  const { explorerData, setExplorerData } = useExplorerContext();
  const { explorerId } = explorerData;

  const [loading, setLoading] = useState(false);
  const [resultsData, setResultsData] = useState(null);

  useEffect(() => {
    // Fetch the results data
    if (explorerId) {
      // Fetch the results data
    }
  }, [explorerId]);

  return (
    <Box>
      <Box>Visualize</Box>
    </Box>
  );
}

StepVisualize.propTypes = {};

export default StepVisualize;
