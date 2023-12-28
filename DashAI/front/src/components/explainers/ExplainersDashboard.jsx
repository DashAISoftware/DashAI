import React from "react";
import { Grid } from "@mui/material";
import { useParams } from "react-router-dom";
import CustomLayout from "../custom/CustomLayout";

export default function ExplainersDashboard() {
  const { id } = useParams();
  return (
    <CustomLayout>
      <Grid container spacing={2}>
        <Grid item>
          <h1>JoJo TE AMO</h1>
        </Grid>
        <Grid item>
          <h1>id: {id}</h1>
        </Grid>
      </Grid>
    </CustomLayout>
  );
}
