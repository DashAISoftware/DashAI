import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import ExperimentsList from "../components/results/ExperimentsList";
import RunsTable from "../components/results/RunsTable";
import { Grid } from "@mui/material";
/**
 * This component renders a table that shows the runs of the experiments and a drawer to select the experiment to visualize
 */
function ResultsPage() {
  // gets the id of the selected experiment in the url
  const { id } = useParams();

  const [appBarHeight, setAppBarHeight] = useState(0);

  // on mount gets the height of the AppBar to adjust the size of the list of experiments to the screen.
  useEffect(() => {
    function updateAppBarHeight() {
      const appBar = document.querySelector("header.MuiAppBar-root");
      const height = appBar?.getBoundingClientRect().height || 0;
      setAppBarHeight(height);
    }

    updateAppBarHeight();

    function handleResize() {
      updateAppBarHeight();
    }

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <Grid
      container
      direction="row"
      wrap="nowrap"
      sx={{
        width: "100vw",
        marginLeft: "calc(-50vw + 50%)",
        my: -5,
      }}
      columnSpacing={2}
    >
      <Grid
        item
        sx={{
          backgroundColor: "#212121",
          height: `calc(100vh - ${appBarHeight}px)`,
        }}
      >
        <ExperimentsList />
      </Grid>
      <Grid item sx={{ my: 5 }}>
        <RunsTable experimentId={id} />
      </Grid>
    </Grid>
  );
}

export default ResultsPage;
