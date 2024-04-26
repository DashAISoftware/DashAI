import React, { useState } from "react";
import PropTypes from "prop-types";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import { Button, Grid, Paper, Tab, Tabs, Typography } from "@mui/material";
import CustomLayout from "../custom/CustomLayout";
import NewGlobalExplainerModal from "./NewGlobalExplainerModal";
import ExplainersGrid from "./ExplainersGrid";

const tabs = [
  { label: "Global Explanations", value: 0, disabled: false },
  { label: "Local Explanations", value: 1, disabled: false },
];

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
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const explainerConfig = {
    runId: id,
  };

  const ExplainersTable = ({ scope, handleNewExplainer, description }) => {
    return (
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
              {scope.charAt(0).toUpperCase() + scope.slice(1)} explanations
            </Typography>
            <Grid item>
              <Button
                variant="contained"
                onClick={handleNewExplainer}
                endIcon={<AddIcon />}
              >
                Add {scope} Explainer
              </Button>
            </Grid>
          </Grid>
          <Typography variant="h6" component="h2">
            {description}
          </Typography>
          <ExplainersGrid runId={id} scope={scope} />
        </Paper>
      </Grid>
    );
  };
  ExplainersTable.propTypes = {
    scope: PropTypes.string.isRequired,
    handleNewExplainer: PropTypes.func.isRequired,
    description: PropTypes.string.isRequired,
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
      <Tabs value={currentTab} onChange={handleTabChange}>
        {tabs.map((tab) => (
          <Tab
            key={tab.value}
            value={tab.value}
            label={tab.label}
            disabled={tab.disabled}
          />
        ))}
      </Tabs>
      <Grid container spacing={2}>
        {currentTab === 0 && (
          <ExplainersTable
            scope={"global"}
            handleNewExplainer={handleNewGlobalExplainerModal}
            description={
              "Global explanations explain how a model bahaves generally."
            }
          />
        )}
        {currentTab === 1 && (
          <ExplainersTable
            scope={"local"}
            handleNewExplainer={handleNewGlobalExplainerModal}
            description={
              "Local explanations explain model predictions for an specific instance."
            }
          />
        )}
      </Grid>
    </CustomLayout>
  );
}
