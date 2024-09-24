import React, { Fragment, useCallback, useEffect, useState } from "react";
import PropTypes from "prop-types";

import {
  Box,
  Button,
  CircularProgress,
  Stack,
  Typography,
} from "@mui/material";

import { createExplorer, getExplorerById } from "../../../api/explorer";
import { enqueueExplorerJob } from "../../../api/job";
import { ExplorerStatus } from "../../../types/explorer";
import { useExplorerContext } from "../context";
import { formatDate } from "../../../utils";

const steps = [
  {
    name: "create",
    header: "Create",
    buttonLabel: "Create Explorer",
  },
  {
    name: "launch exploration",
    header: "Launch Exploration",
    buttonLabel: "Launch Exploration",
  },
  {
    name: "wait for finish",
    header: "Waiting for Finish",
    buttonLabel: "Refresh",
  },
  {
    name: "finished",
    header: "Finished",
  },
];

function StepCreateLaunch({ onExplorationFinished = () => {} }) {
  const { explorerData, setExplorerData, setExplorerId, setFeedback } =
    useExplorerContext();
  const {
    datasetId,
    explorerId,
    selectedColumns,
    selectedExplorer,
    explorerConfig,
    explorationName,
    status,
  } = explorerData;

  const getActiveStep = (status) => {
    switch (status) {
      // Explorer created but not launched
      case ExplorerStatus.NOT_STARTED:
      case ExplorerStatus.ERROR:
        return 1;
      // Explorer launched but not finished
      case ExplorerStatus.DELIVERED:
      case ExplorerStatus.STARTED:
        return 2;
      // Explorer finished
      case ExplorerStatus.FINISHED:
        return 3;
      // Default to create step
      default:
        return 0;
    }
  };

  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(getActiveStep(status));
  const [explorerStatusDisplay, setExplorerStatusDisplay] = useState({
    datetime: "",
    statusDisplay: "",
  });

  const getLastUpdateDateTime = useCallback((explorer) => {
    let datetime = "";
    switch (explorer.status) {
      case ExplorerStatus.NOT_STARTED:
        datetime = explorer.created;
        break;
      case ExplorerStatus.DELIVERED:
        datetime = explorer.delivery_time;
        break;
      case ExplorerStatus.STARTED:
        datetime = explorer.start_time;
        break;
      case ExplorerStatus.FINISHED:
        datetime = explorer.end_time;
        break;
      case ExplorerStatus.ERROR:
        datetime = explorer.start_time;
        break;
      default:
        return "";
    }
    return formatDate(datetime);
  }, []);

  const handleCreateExplorer = () => {
    if (!selectedExplorer) {
      return;
    }
    setLoading(true);
    createExplorer(
      datasetId,
      selectedColumns,
      selectedExplorer,
      explorerConfig,
      explorationName,
    )
      .then((data) => {
        setExplorerId(data.id);
      })
      .catch((error) => {
        console.log(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleLaunchExploration = () => {
    if (!explorerId) {
      return;
    }
    setLoading(true);
    enqueueExplorerJob(explorerId)
      .then((_) => {
        setExplorerStatusDisplay({
          time: formatDate(new Date()),
          status: ExplorerStatus[ExplorerStatus.DELIVERED],
        });
        setActiveStep(2);
        setFeedback({
          show: true,
          message:
            "Exploration launched successfully.\nRefreshing status every 5 seconds.",
          severity: "info",
        });
      })
      .catch((error) => {
        console.log(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const refreshHandle = () => {
    setLoading(true);
    getExplorerById(explorerId)
      .then((data) => {
        setExplorerData((prev) => ({
          ...prev,
          explorationName: data.name,
          selectedColumns: data.columns,
          selectedExplorer: data.exploration_type,
          explorerConfig: data.parameters,
          status: data.status,
        }));
        setExplorerStatusDisplay({
          time: getLastUpdateDateTime(data),
          status: ExplorerStatus[data.status],
        });

        if (data.status === ExplorerStatus.FINISHED) {
          setActiveStep(3);
          setFeedback({
            show: true,
            message: "Exploration finished successfully.",
            severity: "success",
          });
          onExplorationFinished();
        } else if (data.status === ExplorerStatus.ERROR) {
          setFeedback({
            show: true,
            message: "Error occurred during exploration",
            severity: "error",
          });
        }
      })
      .catch((error) => {
        console.log(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // Refresh status every 5 seconds
  useEffect(() => {
    if (activeStep === 2) {
      refreshHandle();
      const interval = setInterval(() => {
        refreshHandle();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [activeStep]);

  return (
    <Box
      sx={{
        height: "100%",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Typography variant="h4" gutterBottom>
        {steps[activeStep].header}
      </Typography>

      {activeStep === 0 && (
        <Button
          variant="contained"
          color="primary"
          onClick={handleCreateExplorer}
          disabled={loading}
        >
          {loading ? (
            <CircularProgress size={24} />
          ) : (
            steps[activeStep].buttonLabel
          )}
        </Button>
      )}

      {activeStep === 1 && (
        <Fragment>
          <Typography variant="h6" gutterBottom>
            Explorer created successfully with ID: {explorerId}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={handleLaunchExploration}
            disabled={loading}
          >
            {loading ? (
              <CircularProgress size={24} />
            ) : (
              steps[activeStep].buttonLabel
            )}
          </Button>
        </Fragment>
      )}

      {activeStep === 2 && (
        <Fragment>
          <Typography variant="h6" gutterBottom>
            Exploration launched successfully.
          </Typography>

          <Box sx={{ height: 20 }} />
          <Typography variant="h6" gutterBottom>
            Last known status: {explorerStatusDisplay.status}
          </Typography>

          <Typography variant="h6" gutterBottom>
            Time of last status: {explorerStatusDisplay.time}
          </Typography>
          <Box sx={{ height: 20 }} />

          <Stack direction="row" spacing={2}>
            {status === ExplorerStatus.ERROR && (
              <Button
                variant="contained"
                color="primary"
                onClick={handleLaunchExploration}
                disabled={loading}
              >
                Re-Launch
              </Button>
            )}

            <Button
              variant="contained"
              color="primary"
              onClick={refreshHandle}
              disabled={loading}
            >
              {loading ? (
                <CircularProgress size={24} />
              ) : (
                steps[activeStep].buttonLabel
              )}
            </Button>
          </Stack>
        </Fragment>
      )}

      {activeStep === 3 && (
        <Fragment>
          <Typography variant="h6" gutterBottom>
            Exploration finished successfully.
          </Typography>
        </Fragment>
      )}
    </Box>
  );
}

StepCreateLaunch.propTypes = {
  onExplorationFinished: PropTypes.func,
};

export default StepCreateLaunch;
