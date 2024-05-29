import { React, useEffect, useState } from "react";
import { Grid } from "@mui/material";
import { useSnackbar } from "notistack";

import { getExplainers as getExplainersRequest } from "../../api/explainer";

import ExplainersCard from "./ExplanainersCard";
import useUpdateFlag from "../../hooks/useUpdateFlag";
import { flags } from "../../constants/flags";

/**
 * GlobalExplainersGrid
 * @returns Grid component for the explainers
 */
export default function ExplainersGrid(explainerConfig) {
  const { enqueueSnackbar } = useSnackbar();
  // const [loading, setLoading] = useState(false);
  const [explainers, setExplainers] = useState([]);
  const { runId, scope } = explainerConfig;

  // Filter explainers that have status FINISHED
  function getFilteredExplainers(explainers) {
    return explainers.filter((explainer) => explainer.status === 3);
  }

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

  useUpdateFlag({
    flag: flags.EXPLAINERS,
    updateFunction: getExplainers,
  });

  useEffect(() => {
    getExplainers();
  }, []);

  return (
    <Grid
      container
      flex={true}
      flexWrap={"nowrap"}
      direction={"column"}
      overflow={"auto"}
      rowGap={5}
      justifyContent="center"
      alignItems="center"
    >
      {getFilteredExplainers(explainers).map((explainer, i) => (
        <ExplainersCard explainer={explainer} key={i} scope={scope} />
      ))}
    </Grid>
  );
}
