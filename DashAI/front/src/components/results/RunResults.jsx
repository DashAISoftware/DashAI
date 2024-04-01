import { useSnackbar } from "notistack";
import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Tabs, Tab, Typography, Paper, Box, Button } from "@mui/material";
import { getRunById as getRunByIdRequest } from "../../api/run";
import RunInfoTab from "./RunInfoTab";
import RunParametersTab from "./RunParametersTab";
import RunMetricsTab from "./RunMetricsTab";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import CustomLayout from "../custom/CustomLayout";

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
function RunResults( {runId} ) {
  const { enqueueSnackbar } = useSnackbar();

  const [runData, setRunData] = useState({});
  const [updateDataFlag, setUpdateDataFlag] = useState({});
  const [currentTab, setCurrentTab] = useState(0);
  const [customLayoutOpen, setCustomLayoutOpen] = useState(true);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const handleCloseCustomLayout = () => {
    setCustomLayoutOpen(false);
  };

  const getRunById = async (runId) => {
    try {
      const run = await getRunByIdRequest(runId);
      setRunData(run);
    } catch (error) {
      enqueueSnackbar(`Error while trying to obtain data of the run id: ${runId}`);
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  // triggers an update of the run data when updateFlag is set to true
  useEffect(() => {
    if (updateDataFlag) {
      setUpdateDataFlag(false);
      getRunById(runId);
    }
  }, [updateDataFlag]);

  // on mount, fetch the data of the run
  useEffect(() => {
    getRunById(runId);
  }, []);
  return (
    <>
      {customLayoutOpen && (
        <CustomLayout>
          <Button
            startIcon={<ArrowBackIosNewIcon />}
            onClick={handleCloseCustomLayout}
          >
            Close
          </Button>

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
              {currentTab === 2 && (
                <RunMetricsTab
                  runData={runData}
                  setUpdateDataFlag={setUpdateDataFlag}
                />
              )}
              {currentTab === 3 && <Typography>TODO...</Typography>}
              {currentTab === 4 && <Typography>TODO...</Typography>}
            </Box>
          </Paper>
        </CustomLayout>
      )}
    </>
  );
}

RunResults.propTypes = {
  runId: PropTypes.number,
};

RunResults.defaultProps = {
  runId: undefined,
};

export default RunResults;
