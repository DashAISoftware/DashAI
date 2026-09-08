import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import { Box, Collapse, Divider } from "@mui/material";
import { useParams } from "react-router-dom";

import LiveMetricsChart from "./LiveMetricsChart";
import HyperparameterPlots from "./HyperparameterPlots";
import { checkHowManyOptimazers } from "../../utils/schema";
import { isRunActive } from "../../utils/runStatus";
import { useModels } from "./ModelsContext";
import useRunResultsData from "./runResults/useRunResultsData";
import ResultsTabsHeader from "./runResults/ResultsTabsHeader";
import ExplainerResultsTab from "./runResults/ExplainerResultsTab";
import PredictionResultsTab from "./runResults/PredictionResultsTab";
import ModelVisualizationTab from "./runResults/ModelVisualizationTab";
import FoldMetricsChart from "./FoldMetricsChart";
import OuterFoldMetricsTable from "./OuterFoldMetricsTable";

/**
 * Shows a run's results as two tab groups (metrics: live/hyperparameters,
 * operations: explainability/predictions). The data layer lives in
 * useRunResultsData; each tab body is its own component. This component wires
 * them together and owns only the view level state: which tab is active,
 * whether the (inline) panel is expanded, the scroll container the explainer
 * list virtualizes against, and the dataset-prediction dialog visibility.
 */
export default function RunResults({
  run,
  session,
  onRefresh,
  explainerRefreshTrigger,
  resultsVisible: controlledVisible = undefined,
  setResultsVisible: setControlledVisible = undefined,
  autoExpand = false,
  fillHeight = false,
  supportsModelArtifacts = false,
}) {
  const isControlled = controlledVisible !== undefined;

  const {
    globalExplainers,
    localExplainers,
    predictions,
    activeExplainers,
    explainerFilter,
    setExplainerFilter,
    newExplainerKey,
    setNewExplainerKey,
    highlightedExplainerKey,
    setHighlightedExplainerKey,
    explainerDisplayNames,
    cardHeightsRef,
    getCacheEntry,
    updateCacheEntry,
    predictionDisplayNumbers,
    outputColumn,
    modelSessionDetail,
    trainingDatasetSample,
    fetchOperations,
    handlePredictionCreated,
    handleExplainerDeleted,
    handlePredictionDeleted,
  } = useRunResultsData({ run, session, onRefresh, explainerRefreshTrigger });

  const [internalVisible, setInternalVisible] = useState(() => {
    if (run.status === 0) return false;
    const saved = localStorage.getItem(`run-${run.id}-results-visible`);
    return saved ? JSON.parse(saved) : false;
  });
  const resultsVisible = isControlled ? controlledVisible : internalVisible;
  const setResultsVisible = isControlled
    ? setControlledVisible
    : setInternalVisible;

  // Always land on Live Metrics (tab 0) when a run's results are shown -
  // no per-run "last tab" persistence, so opening a model card is predictable.
  const [activeTab, setActiveTab] = useState(0);

  // Detail view scroll container, kept in state so the explainer list receives
  // it as its virtualization scroll parent.
  const [explainerScrollParent, setExplainerScrollParent] = useState(null);
  const [showDatasetPanel, setShowDatasetPanel] = useState(false);

  const optimizables = checkHowManyOptimazers({ params: run.parameters });
  const isFinished = run.status === 3;
  const isRunning = isRunActive(run.status);

  useEffect(() => {
    const handleOpenDialog = (event) => {
      if (event.detail.runId === run.id) {
        setResultsVisible(true);
        setActiveTab(2);
        setShowDatasetPanel(true);
      }
    };
    window.addEventListener("openPredictionDialog", handleOpenDialog);
    return () =>
      window.removeEventListener("openPredictionDialog", handleOpenDialog);
  }, [run.id]);

  useEffect(() => {
    if (isRunning && autoExpand) {
      setResultsVisible(true);
      setActiveTab(0); // Live Metrics tab
    }
  }, [isRunning, autoExpand]);

  useEffect(() => {
    if (isControlled) return;
    localStorage.setItem(
      `run-${run.id}-results-visible`,
      JSON.stringify(resultsVisible),
    );
  }, [resultsVisible, run.id, isControlled]);

  // Expose the active tab while this run is shown full screen, so the right
  // sidebar can swap its content (e.g. list explainers on the explainers tab).
  const params = useParams();
  const modelsContext = useModels();
  const setRunDetailTab = modelsContext?.setRunDetailTab;
  const isDetailView = String(params.runId ?? "") === String(run.id);
  useEffect(() => {
    if (!isDetailView || !setRunDetailTab) return;
    setRunDetailTab(activeTab);
    return () => setRunDetailTab(null);
  }, [isDetailView, activeTab, setRunDetailTab]);

  const tabsHeader = (
    <ResultsTabsHeader
      activeTab={activeTab}
      onTabChange={setActiveTab}
      isFinished={isFinished}
      optimizables={optimizables}
      explainerCount={globalExplainers.length + localExplainers.length}
      predictionCount={predictions.length}
      supportsModelArtifacts={supportsModelArtifacts}
      run={run}
    />
  );

  const tabContent = (
    <>
      {activeTab === 0 && (
        <Box sx={{ pb: 4 }}>
          <LiveMetricsChart run={run} modelSessionDetail={modelSessionDetail} />
        </Box>
      )}

      {activeTab === 1 && isFinished && (
        <ExplainerResultsTab
          activeExplainers={activeExplainers}
          explainerFilter={explainerFilter}
          setExplainerFilter={setExplainerFilter}
          fillHeight={fillHeight}
          scrollParent={explainerScrollParent}
          explainerDisplayNames={explainerDisplayNames}
          cardHeightsRef={cardHeightsRef}
          getCacheEntry={getCacheEntry}
          updateCacheEntry={updateCacheEntry}
          newExplainerKey={newExplainerKey}
          setNewExplainerKey={setNewExplainerKey}
          highlightedExplainerKey={highlightedExplainerKey}
          setHighlightedExplainerKey={setHighlightedExplainerKey}
          onDelete={handleExplainerDeleted}
        />
      )}

      {activeTab === 2 && isFinished && (
        <PredictionResultsTab
          run={run}
          session={session}
          predictions={predictions}
          predictionDisplayNumbers={predictionDisplayNumbers}
          outputColumn={outputColumn}
          trainingDatasetSample={trainingDatasetSample}
          showDatasetPanel={showDatasetPanel}
          setShowDatasetPanel={setShowDatasetPanel}
          onSaved={handlePredictionCreated}
          onDelete={handlePredictionDeleted}
          onUpdate={fetchOperations}
        />
      )}

      {activeTab === 3 && isFinished && optimizables > 0 && (
        <Box sx={{ pb: 4 }}>
          <HyperparameterPlots run={run} />
        </Box>
      )}

      {activeTab === 4 && isFinished && (
        <Box sx={{ pb: 4 }}>
          <FoldMetricsChart run={run} />
        </Box>
      )}

      {activeTab === 5 && isFinished && (
        <Box sx={{ pb: 4 }}>
          <OuterFoldMetricsTable run={run} />
        </Box>
      )}

      {activeTab === 6 && isFinished && supportsModelArtifacts && (
        <ModelVisualizationTab run={run} />
      )}
    </>
  );

  // Detail view: fixed header and tabs, only the content scrolls. Card list
  // view keeps the collapsible, content sized layout.
  if (fillHeight) {
    return (
      <Box
        id={`run-results-${run.id}`}
        sx={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          minHeight: 0,
        }}
      >
        <Box sx={{ flexShrink: 0 }}>
          {tabsHeader}
          <Divider sx={{ my: 4 }} />
        </Box>
        <Box
          ref={setExplainerScrollParent}
          sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}
        >
          {tabContent}
        </Box>
      </Box>
    );
  }

  return (
    <Box id={`run-results-${run.id}`}>
      <Collapse in={resultsVisible} timeout="auto" unmountOnExit>
        {tabsHeader}
        <Divider sx={{ my: 4 }} />
        {tabContent}
      </Collapse>
    </Box>
  );
}

RunResults.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string,
    model_name: PropTypes.string,
    status: PropTypes.number,
    experiment_id: PropTypes.number,
    parameters: PropTypes.object,
    model_session_id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    test_metrics: PropTypes.object,
  }).isRequired,
  session: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    task_name: PropTypes.string,
  }),
  onRefresh: PropTypes.func,
  explainerRefreshTrigger: PropTypes.number,
  resultsVisible: PropTypes.bool,
  setResultsVisible: PropTypes.func,
  autoExpand: PropTypes.bool,
  fillHeight: PropTypes.bool,
  supportsModelArtifacts: PropTypes.bool,
};
