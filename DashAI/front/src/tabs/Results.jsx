import React from "react";
import { Typography } from "@mui/material";
import RunsTable from "../components/RunsTable";
import { useParams } from "react-router-dom";
import ExperimentsDrawer from "../components/ExperimentsDrawer";

function Results() {
  const { id } = useParams();
  return (
    <React.Fragment>
      <ExperimentsDrawer />
      <Typography variant="h5">{`Runs table for experiment ${id}`}</Typography>
      <RunsTable experimentId={id} />
    </React.Fragment>
  );
}

export default Results;
