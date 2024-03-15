import React from "react";
import CustomLayout from "../components/custom/CustomLayout";
import { Grid } from "@mui/material";

export default function Test() {
  return (
    <CustomLayout>
      <Grid container spacing={2}>
        <Grid item>
          <h1>testing....</h1>
        </Grid>
        <Grid item>
          <h1> siuu</h1>
        </Grid>
      </Grid>
    </CustomLayout>
  );
}
