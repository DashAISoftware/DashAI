import React, { useCallback, useEffect, useState } from "react";

import {
  Stepper,
  Step,
  StepLabel,
  Button,
  Stack,
  Box,
  Alert,
  Tab,
  Tabs,
  Typography,
  CircularProgress,
} from "@mui/material";
import {
  History as HistoryIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";

import { ExplorerStatus } from "../../types/explorer";
import { getExplorerById } from "../../api/explorer";
import { useExplorerContext } from "./context";
import {
  RecentExplorations,
  StepSelectColumns,
  StepSelectExplorer,
  StepConfiguration,
  StepCreateLaunch,
  StepVisualize,
} from "./";

const steps = [
  {
    name: "selectColumns",
    label: "Select Columns",
  },
  { name: "SelectExplorer", label: "Select Exploration" },
  { name: "Configuration", label: "Configurate" },
  { name: "Create&Launch", label: "Create & Launch" },
  { name: "Visualize", label: "Visualize", hideStepper: true },
];

const tabs = [
  {
    name: "History",
    label: "Recent",
    icon: <HistoryIcon />,
    title: "Select a recent exploration",
    body: "It will retrieve the result, and offer to take it as a template to create a new exploration.",
    reloader: true,
  },
  { name: "Create", label: "Create", icon: <AddIcon />, steps: steps },
];

function Explorer({}) {
  const { explorerData, setExplorerData, feedback, setFeedback } =
    useExplorerContext();
  const { explorerId, selectedExplorer } = explorerData;

  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(1);
  const [activeStep, setActiveStep] = useState(0);

  const [updateRecentExplorations, setUpdateRecentExplorations] =
    useState(false);

  const handleTabChange = (_, newValue) => {
    setFeedback({ ...feedback, show: false });
    setActiveTab(newValue);
  };

  const handleDuplicate = () => {
    // preserve explorerData except for status and explorerId
    setExplorerData((prev) => ({
      ...prev,
      status: null,
      explorerId: null,
      explorationName: `${prev.explorationName}_copy`,
    }));
    handlePreviousStep();
  };

  const handlePreviousStep = () => {
    if (activeStep === 0) {
      return;
    }

    if (activeStep <= steps.length - 2 && explorerId !== null) {
      setFeedback({
        show: true,
        type: "info",
        message: "modifying values will not affect the selected exploration",
      });
      setActiveStep((prev) => prev - 1);
      return;
    }

    setFeedback({ ...feedback, show: false });
    setActiveStep((prev) => prev - 1);
  };

  const handleNextStep = () => {
    if (activeStep === tabs[activeTab].steps.length - 1) {
      return;
    }

    // if explorerId is not null and not in the launch step, skip to the launch step
    if (explorerId !== null && activeStep < steps.length - 2) {
      setActiveStep(steps.length - 2);
      setFeedback({ ...feedback, show: false });
      return;
    }

    if (activeStep === 1) {
      if (!selectedExplorer) {
        setFeedback({
          show: true,
          type: "error",
          message: "You must select explorerType",
        });
        return;
      }
    }

    setFeedback({ ...feedback, show: false });
    setActiveStep((prev) => prev + 1);
  };

  const handleReload = () => {
    if (activeTab === 0) {
      setUpdateRecentExplorations(true);
    }
  };

  const handleExplorationFinished = () => {
    setActiveStep(steps.length - 1);
  };

  const getCurrentDisplay = (activeTab, activeStep) => {
    if (activeTab === 0) {
      return (
        <RecentExplorations
          updateTableFlag={updateRecentExplorations}
          setUpdateTableFlag={setUpdateRecentExplorations}
        />
      );
    }

    if (activeTab === 1) {
      switch (activeStep) {
        case 0:
          return <StepSelectColumns disableChanges={explorerId !== null} />;
        case 1:
          return <StepSelectExplorer disableChanges={explorerId !== null} />;
        case 2:
          return <StepConfiguration disableChanges={explorerId !== null} />;
        case 3:
          return (
            <StepCreateLaunch
              onExplorationFinished={handleExplorationFinished}
            />
          );
        case 4:
          return <StepVisualize />;
      }
    }
  };

  const getExplorerData = (id) => {
    setLoading(true);
    getExplorerById(id)
      .then((data) => {
        setExplorerData((prev) => ({
          ...prev,
          explorationName: data.name,
          selectedColumns: data.columns,
          selectedExplorer: data.exploration_type,
          explorerConfig: data.parameters,
          status: data.status,
        }));

        // change tab and step
        if (ExplorerStatus[data.status] === ExplorerStatus.FINISHED) {
          setActiveStep(steps.length - 1); // show visualize step
        } else {
          setActiveStep(steps.length - 2); // show create & launch step (waiting for result)
        }
        setActiveTab(1);
      })
      .catch((err) => {
        console.log(err);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // on explorerId not null and on change, fetch explorer data
  useEffect(() => {
    if (explorerId) {
      getExplorerData(explorerId);
    }
  }, [explorerId]);

  return (
    <React.Fragment>
      <Stack direction="row" alignItems="center" spacing={2}>
        {/* Show tabs */}
        {activeStep === 0 && (
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            sx={{
              minWidth: 30,
              minHeight: 30,
            }}
          >
            {tabs.map((tab) => (
              <Tab
                key={tab.name}
                label={tab.label || ""}
                icon={tab.icon}
                sx={{ minWidth: 40, minHeight: 40 }}
                iconPosition="end"
              />
            ))}
          </Tabs>
        )}

        {/* Show titles and body if they exist */}
        {tabs[activeTab].title && (
          <Box sx={{ flexGrow: 1, textAlign: "center" }}>
            <Typography variant="h6" component="div">
              {tabs[activeTab].title}
            </Typography>

            {tabs[activeTab].body && (
              <Typography variant="body1" component="div">
                {tabs[activeTab].body}
              </Typography>
            )}
          </Box>
        )}

        {/* Show reloader */}
        {tabs[activeTab].reloader && (
          <Button variant="contained" onClick={handleReload}>
            <RefreshIcon />
          </Button>
        )}

        {/* Show stepper */}
        {tabs[activeTab].steps &&
          !tabs[activeTab].steps[activeStep].hideStepper && (
            <Stepper
              activeStep={activeStep}
              alternativeLabel
              sx={{ flexGrow: 1 }}
            >
              {tabs[activeTab].steps.map((step) => (
                <Step key={step.name}>
                  <StepLabel>{step.label}</StepLabel>
                </Step>
              ))}
            </Stepper>
          )}
      </Stack>

      <Box
        sx={{
          overflowY: "auto",
          overflowX: "auto",
          mt: 2,
          mb: 2,
          height: "calc(100vh - 350px)",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {loading && <CircularProgress />}

        {!loading && getCurrentDisplay(activeTab, activeStep)}
      </Box>

      <Stack direction="row" justifyContent="space-between">
        {activeTab !== 0 && (
          <Button
            variant="contained"
            disabled={activeStep <= 0}
            onClick={handlePreviousStep}
          >
            Previous
          </Button>
        )}

        {feedback.show && (
          <Alert
            severity={feedback.type}
            onClose={() => setFeedback((prev) => ({ ...prev, show: false }))}
          >
            {feedback.message}
          </Alert>
        )}

        {activeTab !== 0 && activeStep === steps.length - 1 && (
          <Button variant="contained" onClick={handleDuplicate}>
            Duplicate
          </Button>
        )}

        {activeTab !== 0 && activeStep < steps.length - 1 && (
          <Button
            variant="contained"
            disabled={
              activeStep === steps.length - 2 &&
              explorerData.status !== ExplorerStatus.FINISHED
            }
            onClick={handleNextStep}
          >
            {explorerId !== null && activeStep < steps.length - 2
              ? "Skip to Launch"
              : activeStep === steps.length - 2
              ? "View Result"
              : "Next"}
          </Button>
        )}
      </Stack>
    </React.Fragment>
  );
}

export default Explorer;
