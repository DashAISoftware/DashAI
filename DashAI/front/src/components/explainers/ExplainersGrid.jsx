import { React, useEffect, useState } from "react";
import { Grid } from "@mui/material";
import { useSnackbar } from "notistack";

import { getExplainers as getExplainersRequest } from "../../api/explainer";

import GlobalExplainersCard from "./GlobalExplanainersCard";

/**
 * GlobalExplainersGrid
 * @returns Grid component for the explainers
 */
export default function ExplainersGrid(explainerConfig) {
  const { enqueueSnackbar } = useSnackbar();
  // const [loading, setLoading] = useState(false);
  const [explainers, setExplainers] = useState([]);
  const { runId, scope } = explainerConfig;

  const getExplainers = async () => {
    try {
      const explainers = await getExplainersRequest(runId, scope);
      setExplainers(explainers);
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
    getExplainers();
  }, []);

  return (
    <Grid
      container
      flex={true}
      flexWrap={"nowrap"}
      direction={"row"}
      overflow={"auto"}
      columnGap={2}
    >
      {explainers.map((explainer, i) => (
        <GlobalExplainersCard explainer={explainer} key={i} scope={scope} />
      ))}
    </Grid>
  );
}
