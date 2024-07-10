import { useSnackbar } from "notistack";
import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { getRunById as getRunByIdRequest } from "../../../api/run";
import ResultsDetailsLayout from "./ResultsDetailsLayout";

/**
 * Component that renders multiple tabs to visualize the results of a specific run.
 */
function ResultsDetails({ runId }) {
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
      enqueueSnackbar(
        `Error while trying to obtain data of the run id: ${runId}`,
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
        <ResultsDetailsLayout
          runData={runData}
          currentTab={currentTab}
          setUpdateDataFlag={setUpdateDataFlag}
          handleTabChange={handleTabChange}
          handleCloseCustomLayout={handleCloseCustomLayout}
        />
      )}
    </>
  );
}

ResultsDetails.propTypes = {
  runId: PropTypes.number,
};

ResultsDetails.defaultProps = {
  runId: undefined,
};

export default ResultsDetails;
