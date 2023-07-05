import { useSnackbar } from "notistack";
import React, { useEffect, useState } from "react";
import { Tabs, Tab, Typography, Paper, Box, Button } from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";
import { getRunById as getRunByIdRequest } from "../../api/run";
import RunInfoTab from "./RunInfoTab";
import RunParametersTab from "./RunParametersTab";
import RunMetricsTab from "./RunMetricsTab";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";

const tabs = [
  { label: "Info", value: 0, disabled: false },
  { label: "Parameters", value: 1, disabled: false },
  { label: "Metrics", value: 2, disabled: false },
  { label: "Artifacts", value: 3, disabled: true },
  { label: "Predict", value: 4, disabled: false },
];
/**
 * Component that renders multiple tabs to visualize the results of a specific run.
 */
function RunResults() {
  const { id } = useParams();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const [runData, setRunData] = useState({});
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const getRunById = async (id) => {
    try {
      const run = await getRunByIdRequest(id);
      setRunData(run);
    } catch (error) {
      enqueueSnackbar(
        `Error while trying to obtain data of the run id: ${id}`,
        {
          variant: "error",
          anchorOrigin: {
            vertical: "top",
            horizontal: "right",
          },
        },
      );
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    }
  };
  // on mount, fetch the data of the run
  useEffect(() => {
    getRunById(id);
  }, []);
  return (
    <React.Fragment>
      {/* Button to return to the experiment results table */}
      <Button
        startIcon={<ArrowBackIosNewIcon />}
        onClick={() => {
          navigate(`/app/results/experiments/${runData.experiment_id}`);
        }}
      >
        Return to table
      </Button>

      {/* Tabs  */}
      <Paper sx={{ mt: 2 }}>
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
        <Box sx={{ p: 3, height: "100%" }}>
          {currentTab === 0 && <RunInfoTab runData={runData} />}
          {currentTab === 1 && <RunParametersTab runData={runData} />}
          {currentTab === 2 && <RunMetricsTab runData={runData} />}
          {currentTab === 3 && <Typography>TODO...</Typography>}
          {currentTab === 4 && <Typography>TODO...</Typography>}
        </Box>
      </Paper>
    </React.Fragment>
  );
}

export default RunResults;
