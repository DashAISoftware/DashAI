import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  getRuns as getRunsRequest,
  getHyperparameterPlot as getHyperparameterPlotRequest,
} from "../../../api/run";
import { getComponents as getComponentsRequest } from "../../../api/component";
import { getExperimentById } from "../../../api/experiment";
import { useSnackbar } from "notistack";
import { getRunStatus } from "../../../utils/runStatus";
import ResultsTableLayout from "./ResultsTableLayout";

// constants
import { extractRows } from "../constants/extractRows";
import { extractColumns } from "../constants/extractColumns";

/**
 * This component renders a table that contains the runs associated to an experiment.
 * @param {string} experimentId id of the experiment whose runs the user wants to analyze.
 */
function ResultsTable({ experimentId }) {
  const { enqueueSnackbar } = useSnackbar();

  const [rows, setRows] = useState([]);
  const [columns, setColumns] = useState([]);
  const [columnGroupingModel, setColumnGroupingModel] = useState([]);
  const [columnVisibilityModel, setColumnVisibilityModel] = useState({});
  const [loading, setLoading] = useState(false);
  const [showRunResults, setShowRunResults] = useState(false);
  const [selectedRunId, setSelectedRunId] = useState(null);

  const handleRunResultsOpen = (runId) => {
    setSelectedRunId(runId);
    setShowRunResults(true);
  };

  const handleCloseRunResults = () => {
    setShowRunResults(false);
  };

  const getRuns = async () => {
    setLoading(true);
    try {
      const runs = await getRunsRequest(experimentId);
      const experiment = await getExperimentById(experimentId);
      const metrics = await getComponentsRequest({
        selectTypes: ["Metric"],
        relatedComponent: experiment.task_name,
      });
      const rows = extractRows(runs);
      const rowsWithStringStatus = rows.map((run) => {
        return { ...run, status: getRunStatus(run.status) };
      });
      const { columns, columnGroupingModel, columnVisibilityModel } =
        extractColumns(metrics, runs, handleRunResultsOpen);
      setRows(rowsWithStringStatus);
      setColumns(columns);
      setColumnGroupingModel(columnGroupingModel);
      setColumnVisibilityModel(columnVisibilityModel);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the runs table.");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  // fetch the runs and preprocess the data for DataGrid
  useEffect(() => {
    if (experimentId !== undefined) {
      getRuns();
      setShowRunResults(false);
      setSelectedRunId(null);
    }
  }, [experimentId]);

  return (
    <ResultsTableLayout
      experimentId={experimentId}
      rows={
        experimentId
          ? rows.filter((run) => String(run.experiment_id) === experimentId)
          : []
      }
      columns={columns}
      showRunResults={showRunResults}
      loading={loading}
      selectedRunId={selectedRunId}
      handleCloseRunResults={handleCloseRunResults}
      columnVisibilityModel={columnVisibilityModel}
      columnGroupingModel={columnGroupingModel}
    />
  );
}

ResultsTable.propTypes = {
  experimentId: PropTypes.string,
};

ResultsTable.defaultProps = {
  experimentId: undefined,
};

export default ResultsTable;
