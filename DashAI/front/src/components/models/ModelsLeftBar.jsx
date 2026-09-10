import React, { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Box, Divider, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import Biotech from "@mui/icons-material/Biotech";
import ViewModuleIcon from "@mui/icons-material/ViewModule";
import Footer from "../threeSectionLayout/Footer";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import DatasetFolderList from "../threeSectionLayout/DatasetFolderList";
import GroupedCollapsibleList from "../threeSectionLayout/GroupedCollapsibleList";
import SearchBar from "../threeSectionLayout/SearchBar";
import NewItemButton from "../threeSectionLayout/NewItemButton";
import InfoSessionModal from "./InfoSessionModal";
import { useTranslation } from "react-i18next";
import { useModels } from "./ModelsContext";

export default function ModelsLeftBar({ onToggle }) {
  const {
    deleteSessionById,
    deleteSessionsByIds,
    setSelectedSessionId,
    setSelectedSession,
    setSelectedTask,
    setStep,
    selectDataset,
    datasets,
    selectedDatasetId,
    replaceDatasets,
    sessions,
    tasks,
    selectedSessionId,
    setSessions,
    deleteDataset,
    deleteDatasetsByIds,
    editDataset,
    editSession,
    folders,
    createFolder,
    renameFolder,
    deleteFolderById,
    moveDatasetToFolder,
    openSections,
    setOpenSections,
    openFolderIds,
    setOpenFolderIds,
  } = useModels();
  const navigate = useNavigate();

  const theme = useTheme();
  const [searchQuery, setSearchQuery] = useState("");
  const [filteredDatasets, setFilteredDatasets] = useState(datasets);
  const [filteredSessions, setFilteredSessions] = useState(sessions);
  const [selectedInfoSession, setSelectedInfoSession] = useState(null);
  const { t } = useTranslation(["models", "datasets", "common"]);

  const SEARCH_THRESHOLD = 10;
  const totalItems = datasets.length + sessions.length;

  useEffect(() => {
    if (totalItems <= SEARCH_THRESHOLD) setSearchQuery("");
  }, [totalItems]);

  const getTaskDisplayName = React.useCallback(
    (taskName) => {
      if (!taskName) return t("common:other");
      const task = tasks.find((t) => t.name === taskName);
      return (
        task?.metadata?.display_name ||
        taskName
          .replace("Task", "")
          .replace(/([A-Z])/g, " $1")
          .trim()
      );
    },
    [tasks],
  );

  useEffect(() => {
    // Sync the section map with the current task display names
    const displayNames = [
      ...new Set(
        sessions.map((session) => getTaskDisplayName(session.task_name)),
      ),
    ];
    setOpenSections((prev) => {
      // Only update if display names have changed
      const prevKeys = Object.keys(prev).sort().join(",");
      const newKeys = displayNames.slice().sort().join(",");
      if (prevKeys === newKeys) return prev;
      // Preserve existing open/close state; initialize new keys as closed
      const merged = {};
      displayNames.forEach((displayName) => {
        merged[displayName] = displayName in prev ? prev[displayName] : false;
      });
      return merged;
    });
  }, [sessions, tasks]);

  useEffect(() => {
    const q = searchQuery.trim().toLowerCase();

    if (!q) {
      setFilteredDatasets(datasets);
      setFilteredSessions(sessions);
      return;
    }

    const match = (item) => (item?.name ?? "").toLowerCase().includes(q);

    setFilteredDatasets(datasets.filter(match));
    setFilteredSessions(sessions.filter(match));
  }, [searchQuery, datasets, sessions]);

  const handleSearchChange = (e) => setSearchQuery(e.target.value);

  const handleSessionInfo = React.useCallback(
    (sessionId) => {
      const session = sessions.find((s) => s.id === sessionId);
      if (session) {
        setSelectedInfoSession(session);
      }
    },
    [sessions],
  );

  const getDatasetDeleteConfirmationContent = (dataset) =>
    t(
      "datasets:label.confirmDeleteDataset",
      'Are you sure you want to delete the dataset "{{name}}"? This action cannot be undone.',
      { name: dataset.name },
    );

  const getDatasetDeleteConfirmationWarning = () =>
    t(
      "datasets:label.confirmDeleteDatasetLinkedWarning",
      "All notebooks and sessions linked to this dataset will also be deleted.",
    );

  const getSessionDeleteConfirmationContent = (session) =>
    t(
      "models:label.confirmDeleteSession",
      'Are you sure you want to delete the session "{{name}}"? This action cannot be undone.',
      { name: session.name },
    );

  const getSessionBulkDeleteConfirmationContent = (count) =>
    t("models:label.confirmBulkDeleteSessions", {
      count,
      defaultValue:
        "Are you sure you want to delete the {{count}} selected sessions? This action cannot be undone.",
    });

  const TASK_TRANSLATIONS = {
    tabularClassification: () => t("datasets:task.tabularClassification"),
    imageClassification: () => t("datasets:task.imageClassification"),
    textClassification: () => t("datasets:task.textClassification"),
    translation: () => t("datasets:task.translation"),
    regression: () => t("datasets:task.regression"),
    eda: () => t("datasets:task.eda"),
  };

  const TASK_KEY_MAP = {
    "Tabular Classification": "tabularClassification",
    "Image Classification": "imageClassification",
    "Text Classification": "textClassification",
    Translation: "translation",
    Regression: "regression",
    EDA: "eda",
  };

  const getDatasetDescription = (dataset) => {
    const base = t("datasets:label.datasetDescription", {
      rows: dataset.total_rows || 0,
      columns: dataset.total_columns || 0,
    });
    if (!dataset.task) return base;
    const key = TASK_KEY_MAP[dataset.task];
    const taskLabel = TASK_TRANSLATIONS[key]
      ? TASK_TRANSLATIONS[key]()
      : dataset.task;
    return `${taskLabel} | ${base}`;
  };

  const getSessionDescription = (session) => {
    if (session.dataset_id && datasets.length > 0) {
      const associatedDataset = datasets.find(
        (dataset) => dataset.id === session.dataset_id,
      );

      return associatedDataset?.name
        ? `from ${associatedDataset.name} dataset`
        : "No dataset";
    }
    return session.description || "";
  };

  // Group sessions by task, sorted to maintain a consistent order.
  // Memoized so the object identity stays stable across renders that don't
  // change the underlying data — GroupedCollapsibleList uses `groups` as an
  // effect dependency, so a fresh literal every render would re-run it.
  const sortedGroupedSessions = useMemo(() => {
    const groupedSessions = filteredSessions?.reduce((groups, session) => {
      const displayName = getTaskDisplayName(session.task_name);
      if (!groups[displayName]) {
        groups[displayName] = [];
      }
      groups[displayName].push(session);
      return groups;
    }, {});

    return groupedSessions
      ? Object.keys(groupedSessions)
          .sort()
          .reduce((sorted, key) => {
            sorted[key] = groupedSessions[key];
            return sorted;
          }, {})
      : {};
  }, [filteredSessions, getTaskDisplayName]);

  const onDatasetClick = (datasetId) => {
    navigate(`/app/models/datasets/${datasetId}`);
  };

  const onSessionDelete = async (id) => {
    const success = await deleteSessionById(id);
    if (!success) return;
    if (id === selectedSessionId) {
      navigate("/app/models");
    }
  };

  const onDatasetDelete = (id) => {
    if (id === selectedDatasetId) {
      navigate("/app/models");
    }

    replaceDatasets((prevDatasets) =>
      prevDatasets.filter((dataset) => dataset.id !== id),
    );

    setSessions((prevSessions) => {
      const filteredSessions = prevSessions.filter(
        (session) => session.dataset_id !== id,
      );

      if (
        selectedSessionId &&
        prevSessions.find(
          (session) =>
            session.id === selectedSessionId && session.dataset_id === id,
        )
      ) {
        navigate("/app/models");
      }

      return filteredSessions;
    });

    deleteDataset(id);
  };

  const onBulkDatasetDelete = async (ids) => {
    const idSet = new Set(ids);
    const success = await deleteDatasetsByIds(ids);
    if (!success) return false;

    const sessionAffected =
      selectedSessionId != null &&
      sessions.some(
        (session) =>
          session.id === selectedSessionId && idSet.has(session.dataset_id),
      );

    setSessions((prevSessions) =>
      prevSessions.filter((session) => !idSet.has(session.dataset_id)),
    );

    if (idSet.has(selectedDatasetId) || sessionAffected) {
      navigate("/app/models");
    }

    return true;
  };

  const onBulkSessionDelete = async (ids) => {
    const success = await deleteSessionsByIds(ids);
    if (!success) return false;
    if (ids.includes(selectedSessionId)) {
      navigate("/app/models");
    }
    return true;
  };

  const onSessionClick = (sessionId) => {
    navigate(`/app/models/sessions/${sessionId}`);
  };

  const handleNewSessionButton = () => {
    navigate("/app/models");
  };

  return (
    <SideBar>
      {/* Create new item button */}
      <Box p={4} sx={{ height: "64px", display: "flex", alignItems: "center" }}>
        {selectedDatasetId || selectedSessionId ? (
          <NewItemButton
            onClick={handleNewSessionButton}
            title={t("models:button.modelsHub")}
            EndIcon={ViewModuleIcon}
          />
        ) : (
          <Typography variant="body1" color="textSecondary">
            {t("models:label.modelsModule")}
          </Typography>
        )}
      </Box>

      {/* Search bar global */}
      {totalItems > SEARCH_THRESHOLD && (
        <Box px={4} pb={4} flex={"0 0 auto"}>
          <SearchBar
            placeholder={t("models:label.searchDatasetsSessions")}
            value={searchQuery}
            onChange={handleSearchChange}
          />
        </Box>
      )}

      <Divider
        sx={{ width: "90%", bgcolor: theme.palette.ui.borderDark, mx: "auto" }}
      />

      {/* Scrollable content */}
      <Box display="flex" flexDirection="column" flex={1} minHeight={0}>
        <DatasetFolderList
          datasets={filteredDatasets}
          folders={folders}
          openFolderIds={openFolderIds}
          setOpenFolderIds={setOpenFolderIds}
          selectedItemId={selectedDatasetId}
          onItemClick={onDatasetClick}
          onItemDelete={onDatasetDelete}
          onItemEdit={editDataset}
          onBulkDelete={onBulkDatasetDelete}
          title={t("datasets:label.availableDatasets")}
          getItemDescription={getDatasetDescription}
          getDeleteConfirmationContent={getDatasetDeleteConfirmationContent}
          getDeleteConfirmationWarning={getDatasetDeleteConfirmationWarning}
          onCreateFolder={createFolder}
          onRenameFolder={renameFolder}
          onDeleteFolder={deleteFolderById}
          onMoveDataset={moveDatasetToFolder}
        />

        <Divider
          sx={{
            width: "90%",
            bgcolor: theme.palette.ui.borderDark,
            mx: "auto",
          }}
        />

        <GroupedCollapsibleList
          groups={sortedGroupedSessions}
          selectedItemId={selectedSessionId}
          onItemClick={onSessionClick}
          onItemDelete={onSessionDelete}
          onItemEdit={editSession}
          onItemInfo={handleSessionInfo}
          title={t("common:sessions")}
          Icon={Biotech}
          getItemDescription={getSessionDescription}
          getDeleteConfirmationContent={getSessionDeleteConfirmationContent}
          openGroups={openSections}
          onOpenGroupsChange={setOpenSections}
          onBulkDelete={onBulkSessionDelete}
          selectItemsTooltip={t(
            "models:label.selectSessionsToDelete",
            "Select sessions to delete",
          )}
          getBulkDeleteConfirmationContent={
            getSessionBulkDeleteConfirmationContent
          }
        />
      </Box>

      {/* Footer */}
      <Footer />

      {/* Session Info Modal */}
      {selectedInfoSession && (
        <InfoSessionModal
          sessionData={selectedInfoSession}
          datasets={datasets}
          tasks={tasks}
          open={!!selectedInfoSession}
          onClose={() => setSelectedInfoSession(null)}
        />
      )}
    </SideBar>
  );
}
