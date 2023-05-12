import React from "react";
import { Grid, Typography } from "@mui/material";
import {
  FileUpload as FileUploadIcon,
  Science as ScienceIcon,
  Assignment as AssignmentIcon,
} from "@mui/icons-material";
import HomeButton from "../components/HomeButton";

function Home() {
  return (
    <React.Fragment>
      {/* Title */}
      <Typography variant="h3" component="h1" sx={{ mb: 6 }}>
        Welcome to DashAI!
      </Typography>
      <Typography variant="h5" component="h2">
        Getting started
      </Typography>
      <Grid
        container
        direction="row"
        justifyContent="flex-start"
        alignItems="center"
        sx={{ mt: 4, mx: 0, maxWidth: "100%" }}
      >
        <Grid item md={4} sm={6} xs={12}>
          <HomeButton
            title="Datasets"
            description="Create and manage the datasets registered in the application."
            to="/app/data"
            Icon={FileUploadIcon}
          />
        </Grid>
        <Grid item md={4} sm={6} xs={12}>
          <HomeButton
            title="Experiments"
            description="Create and manage and view the status of your experiments."
            to="/app/experiments"
            Icon={ScienceIcon}
          />
        </Grid>
        <Grid item md={4} sm={6} xs={12}>
          <HomeButton
            title="Results"
            description={
              "View the results of the models that are being trained and those that \
            have already been trained."
            }
            to="/app/results"
            Icon={AssignmentIcon}
          />
        </Grid>
      </Grid>
    </React.Fragment>
  );
}

export default Home;
