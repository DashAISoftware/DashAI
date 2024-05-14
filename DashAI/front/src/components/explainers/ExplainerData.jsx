import { useSnackbar } from "notistack";
import React, { useEffect, useState } from "react";
import { Tabs, Tab, Paper, Box, Button } from "@mui/material";
import { useNavigate, useParams } from "react-router-dom";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import CustomLayout from "../custom/CustomLayout";
import { getExplainers } from "../../api/explainer";
import ExplainerInfoTab from "./ExplainerInfoTab";
import ExplainerParametersTab from "./ExplainerParametersTab";

const tabs = [
  { label: "Explainer parameters", value: 0, disabled: false },
  { label: "Info", value: 1, disabled: false },
];
/**
 * Component that renders multiple tabs to visualize the results of a specific explainer.
 */
function ExplainerData() {
  const { id, runId, scope } = useParams();
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const [explainerData, setExplainerData] = useState({});
  const [updateDataFlag, setUpdateDataFlag] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const getExplainer = async () => {
    try {
      const explainers = await getExplainers(runId, scope);
      for (let i = 0; i < explainers.length; i++) {
        const explainer = explainers[i];
        if (explainer.id === parseInt(id)) {
          setExplainerData(explainer);
          break;
        }
      }
    } catch (error) {
      enqueueSnackbar(
        `Error while trying to obtain data of the explainer with id: ${id}`,
      );
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  // triggers an update of the explainer data when updateFlag is set to true
  useEffect(() => {
    if (updateDataFlag) {
      setUpdateDataFlag(false);
      getExplainer();
    }
  }, [updateDataFlag]);

  // on mount, fetch the data of the explainer
  useEffect(() => {
    getExplainer();
  }, []);
  return (
    <CustomLayout>
      {/* Button to return to the explainers table */}
      <Button
        startIcon={<ArrowBackIosNewIcon />}
        onClick={() => {
          navigate(`/app/explainers/runs/${explainerData.run_id}`);
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
          {currentTab === 0 && (
            <ExplainerParametersTab explainerData={explainerData} />
          )}
          {currentTab === 1 && (
            <ExplainerInfoTab explainerData={explainerData} />
          )}
        </Box>
      </Paper>
    </CustomLayout>
  );
}

export default ExplainerData;
