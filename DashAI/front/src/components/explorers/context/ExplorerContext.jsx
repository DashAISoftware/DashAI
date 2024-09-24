import React, { createContext, useState, useContext, useCallback } from "react";
import PropTypes from "prop-types";

// Create the context
const ExplorerContext = createContext({
  explorerData: {
    datasetId: null,
    explorerId: null,
    selectedColumns: [],
    selectedExplorer: null,
    explorerConfig: {},
    explorationName: "",
    status: null,
  },
  setExplorerData: () => {},
  feedback: {
    show: false,
    type: "info",
    message: "",
  },
  setFeedback: () => {},
  setSelectedColumns: () => {},
  setSelectedExplorer: () => {},
  setExplorationName: () => {},
  setExplorerConfig: () => {},
  setExplorerId: () => {},
});

// Create a provider component
export function ExplorerProvider({ children, datasetId, explorerId = null }) {
  // Instance variables for the explorer module
  const [explorerData, setExplorerData] = useState({
    datasetId,
    explorerId,
    selectedColumns: [],
    selectedExplorer: null,
    explorerConfig: {},
    explorationName: "",
    status: null,
  });

  // Feedback for the explorer module
  const [feedback, setFeedback] = useState({
    show: false,
    type: "info",
    message: "",
  });

  const setSelectedColumns = (columns) => {
    setExplorerData((prev) => ({ ...prev, selectedColumns: columns }));
  };

  const setSelectedExplorer = (explorer) => {
    setExplorerData((prev) => ({ ...prev, selectedExplorer: explorer }));
  };

  const setExplorationName = (name) => {
    setExplorerData((prev) => ({ ...prev, explorationName: name }));
  };

  const setExplorerConfig = (config) => {
    setExplorerData((prev) => ({ ...prev, explorerConfig: config }));
  };

  const setExplorerId = (id) => {
    setExplorerData((prev) => ({ ...prev, explorerId: id }));
  };

  return (
    <ExplorerContext.Provider
      value={{
        explorerData,
        setExplorerData,
        setSelectedColumns,
        setSelectedExplorer,
        setExplorationName,
        setExplorerConfig,
        setExplorerId,
        feedback,
        setFeedback,
      }}
    >
      {children}
    </ExplorerContext.Provider>
  );
}

ExplorerProvider.propTypes = {
  children: PropTypes.node.isRequired,
  datasetId: PropTypes.number.isRequired,
  explorerId: PropTypes.number,
};

// Create a hook to use the context
export const useExplorerContext = () => {
  const context = useContext(ExplorerContext);
  if (!context.explorerData.datasetId) {
    throw new Error(
      "useExplorerContext must be used within a ExplorerProvider which has a datasetId",
    );
  }
  return context;
};
