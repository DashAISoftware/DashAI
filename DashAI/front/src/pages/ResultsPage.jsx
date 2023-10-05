import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import ExperimentsList from "../components/results/ExperimentsList";
import RunsTable from "../components/results/RunsTable";
import { Grid } from "@mui/material";
import CustomLayout from "../components/custom/CustomLayout";
/**
 * This component renders a table that shows the runs of the experiments and a list to select the experiment to visualize
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
    <CustomLayout disableContainer>
      <Grid
        container
        direction="row"
        wrap="nowrap"
        sx={{
          width: "100vw",
          marginLeft: "calc(-50vw + 50%)",
        }}
        columnSpacing={2}
      >
        {/* List of experiments */}
        <Grid
          item
          xs={2}
          sx={{
            backgroundColor: "#212121",
            height: `calc(100vh - ${appBarHeight}px)`,
          }}
        >
          <ExperimentsList />
        </Grid>

        {/* Runs table */}
        <Grid item xs={10}>
          <CustomLayout>
            <RunsTable experimentId={id} />
          </CustomLayout>
        </Grid>
      </Grid>
    </CustomLayout>
  );
}

export default ResultsPage;
