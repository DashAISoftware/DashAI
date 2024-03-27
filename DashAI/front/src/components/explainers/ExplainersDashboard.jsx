import React, { useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import { Button, Grid, Paper, Typography } from "@mui/material";
import CustomLayout from "../custom/CustomLayout";
import NewGlobalExplainerModal from "./NewGlobalExplainerModal";
import ExplainersGrid from "./ExplainersGrid";

export default function ExplainersDashboard() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { modelName } = location.state;
  const [showNewGlobalExplainerModal, setShowNewGlobalExplainerModal] =
    useState(false);
  const handleNewGlobalExplainerModal = () => {
    setShowNewGlobalExplainerModal(true);
  };

  const explainerConfig = {
    runId: id,
  };

  return (
    <CustomLayout>
      <NewGlobalExplainerModal
        open={showNewGlobalExplainerModal}
        setOpen={setShowNewGlobalExplainerModal}
        explainerConfig={explainerConfig}
      />
      <Typography variant="h4" component="h1" sx={{ mb: 3 }}>
        Explanations dashboard for model: {modelName}, run id: {id}
      </Typography>
      <Button
        startIcon={<ArrowBackIosNewIcon />}
        onClick={() => {
          navigate(`/app/explainers`);
        }}
      >
        Return to table
      </Button>
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <Paper sx={{ py: 2, px: 2 }}>
            <Grid
              container
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ mb: 4 }}
            >
              <Typography variant="h4" component="h2">
                Global explanations
              </Typography>
              <Grid item>
                <Button
                  variant="contained"
                  onClick={handleNewGlobalExplainerModal}
                  endIcon={<AddIcon />}
                >
                  Add Global Explainer
                </Button>
              </Grid>
            </Grid>
            <Typography variant="h6" component="h2">
              Global explanations explain how a model bahaves generally.
            </Typography>
            <ExplainersGrid runId={id} scope={"global"} />
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper sx={{ py: 2, px: 2 }}>
            <Grid
              container
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ mb: 4 }}
            >
              <Typography variant="h4" component="h2">
                Local explanations
              </Typography>
              <Grid item>
                <Button variant="contained" endIcon={<AddIcon />}>
                  Add Local Explainer
                </Button>
              </Grid>
            </Grid>
            <Typography variant="h6" component="h2">
              Local explanations explain model predictions for an specific
              instance.
            </Typography>
            <ExplainersGrid runId={id} scope={"local"} />
          </Paper>
        </Grid>
      </Grid>
    </CustomLayout>
  );
}
