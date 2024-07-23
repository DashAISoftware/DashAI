import React from "react";
import PropTypes from "prop-types";
import { Tabs, Tab, Typography, Paper, Box, Button } from "@mui/material";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import CustomLayout from "../../../components/custom/CustomLayout";
import ResultsTabInfo from "./ResultsTabInfo";
import ResultsTabParameters from "./ResultsTabParameters";
import ResultsTabMetrics from "./ResultsTabMetrics";
import ResultsTabHyperparameters from "./ResultsTabHyperparameters";
import { tabsResultsDetails } from "../constants/tabsResultsDetails";

function ResultsDetailsLayout({
  runData,
  currentTab,
  setUpdateDataFlag,
  handleTabChange,
  handleCloseCustomLayout,
}) {
  return (
    <CustomLayout>
      <Button
        startIcon={<ArrowBackIosNewIcon />}
        onClick={handleCloseCustomLayout}
      >
        Close
      </Button>

      <Paper sx={{ mt: 2 }}>
        <Tabs value={currentTab} onChange={handleTabChange}>
          {tabsResultsDetails.map((tab) => (
            <Tab
              key={tab.value}
              value={tab.value}
              label={tab.label}
              disabled={tab.disabled}
            />
          ))}
        </Tabs>
        <Box sx={{ p: 3, height: "100%" }}>
          {currentTab === 0 && <ResultsTabInfo runData={runData} />}
          {currentTab === 1 && <ResultsTabParameters runData={runData} />}
          {currentTab === 2 && (
            <ResultsTabMetrics
              runData={runData}
              setUpdateDataFlag={setUpdateDataFlag}
            />
          )}
          {currentTab === 3 && <ResultsTabHyperparameters runData={runData} />}
          {currentTab === 4 && <Typography>TODO...</Typography>}
        </Box>
      </Paper>
    </CustomLayout>
  );
}

ResultsDetailsLayout.propTypes = {
  runData: PropTypes.object,
  currentTab: PropTypes.number,
  setUpdateDataFlag: PropTypes.func,
  handleTabChange: PropTypes.func,
  handleCloseCustomLayout: PropTypes.func,
};

export default ResultsDetailsLayout;
