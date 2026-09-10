import { useState, useEffect } from "react";
import { useNavigate, useLocation, useMatch } from "react-router-dom";
import { Box, Divider, Typography } from "@mui/material";
import DescriptionIcon from "@mui/icons-material/Description";
import CloudDownloadIcon from "@mui/icons-material/CloudDownload";
import ViewModuleIcon from "@mui/icons-material/ViewModule";
import Footer from "../threeSectionLayout/Footer";
import CollapsibleList from "../threeSectionLayout/CollapsibleList";
import DatasetFolderList from "../threeSectionLayout/DatasetFolderList";
import SearchBar from "../threeSectionLayout/SearchBar";
import NewItemButton from "../threeSectionLayout/NewItemButton";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import InfoNotebookModal from "./notebook/InfoNotebookModal";
import { useTranslation } from "react-i18next";

import { useDatasetsAndNotebooks } from "../custom/contexts/DatasetsAndNotebooksContext";

export default function DatasetsNotebooksLeftBar({
  onToggle,
  onDownloadDelete,
}) {
  const {
    datasets,
    notebooks,
    selectedDatasetId,
    selectedNotebookId,
    deleteDatasetById,
    deleteDatasetsByIds,
    removeNotebooksByDatasetId,
    editDataset,
    moveDatasetToFolder,
    editNotebook,
    deleteNotebookById,
    deleteNotebooksByIds,
    downloads,
    deleteDownloadById,
    folders,
    createFolder,
    renameFolder,
    deleteFolderById,
    openFolderIds,
    setOpenFolderIds,
  } = useDatasetsAndNotebooks();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const isHub = pathname.startsWith("/app/data/hub");
  const datafileMatch = useMatch("/app/data/hub/import/:datafileId/*");
  const selectedDatafileId = datafileMatch
    ? parseInt(datafileMatch.params.datafileId)
    : null;

  const [filteredDatasets, setFilteredDatasets] = useState(datasets);
  const [filteredNotebooks, setFilteredNotebooks] = useState(notebooks);
  const [filteredDownloads, setFilteredDownloads] = useState(downloads);
  const [selectedInfoNotebook, setSelectedInfoNotebook] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const { t } = useTranslation(["datasets", "common", "hub"]);

  const SEARCH_THRESHOLD = 10;
  const totalItems = datasets.length + notebooks.length + downloads.length;

  useEffect(() => {
    if (totalItems <= SEARCH_THRESHOLD) setSearchQuery("");
  }, [totalItems]);

  useEffect(() => {
    const q = searchQuery.trim().toLowerCase();

    if (!q) {
      setFilteredDatasets(datasets);
      setFilteredNotebooks(notebooks);
      setFilteredDownloads(downloads);
      return;
    }

    const match = (item) => (item?.name ?? "").toLowerCase().includes(q);

    setFilteredDatasets(datasets.filter(match));
    setFilteredNotebooks(notebooks.filter(match));
    setFilteredDownloads(downloads.filter(match));
  }, [searchQuery, datasets, notebooks, downloads]);

  const handleSearchChange = (e) => setSearchQuery(e.target.value);

  const handleNotebookInfo = (notebookId) => {
    const notebook = notebooks.find((n) => n.id === notebookId);
    if (notebook) {
      setSelectedInfoNotebook(notebook);
    }
  };

  const handleDeleteDownload = async (id) => {
    const success = await deleteDownloadById(id);
    if (success) onDownloadDelete?.(id);
  };

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

  const getNotebookDeleteConfirmationContent = (notebook) =>
    t(
      "datasets:label.confirmDeleteNotebook",
      'Are you sure you want to delete the notebook "{{name}}"? This action cannot be undone.',
      { name: notebook.name },
    );

  const getNotebookBulkDeleteConfirmationContent = (count) =>
    t("datasets:label.confirmBulkDeleteNotebooks", {
      count,
      defaultValue:
        "Are you sure you want to delete the {{count}} selected notebooks? This action cannot be undone.",
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
    const base =
      dataset.description ||
      `${dataset.total_rows} ${t("common:rows")}, ${dataset.total_columns} ${t(
        "common:columns",
      )}`;
    if (!dataset.task) return base;
    const key = TASK_KEY_MAP[dataset.task];
    const taskLabel = TASK_TRANSLATIONS[key]
      ? TASK_TRANSLATIONS[key]()
      : dataset.task;
    return `${taskLabel} | ${base}`;
  };

  const getNotebookDescription = (notebook) => {
    if (notebook.dataset_id && datasets.length > 0) {
      const associatedDataset = datasets.find(
        (dataset) => dataset.id === notebook.dataset_id,
      );
      return associatedDataset?.name
        ? t("datasets:label.fromDataset", {
            datasetName: associatedDataset.name,
          })
        : t("datasets:label.noDataset");
    }
    return notebook.description || "";
  };

  const onDatasetClick = (id) => {
    navigate(`/app/data/datasets/${id}`);
  };

  const onNotebookClick = (id) => {
    navigate(`/app/data/notebooks/${id}`);
  };

  const onDatasetDelete = async (id) => {
    const success = await deleteDatasetById(id);
    if (!success) return;
    if (id === selectedDatasetId) {
      navigate("/app/data");
    }
    removeNotebooksByDatasetId(id);
  };

  const onBulkDatasetDelete = async (ids) => {
    const success = await deleteDatasetsByIds(ids);
    if (!success) return false;
    if (ids.includes(selectedDatasetId)) {
      navigate("/app/data");
    }
    ids.forEach((id) => removeNotebooksByDatasetId(id));
    return true;
  };

  const onNotebookDelete = async (id) => {
    const success = await deleteNotebookById(id);
    if (!success) return;
    if (id === selectedNotebookId) {
      navigate("/app/data");
    }
  };

  const onBulkNotebookDelete = async (ids) => {
    const success = await deleteNotebooksByIds(ids);
    if (!success) return false;
    if (ids.includes(selectedNotebookId)) {
      navigate("/app/data");
    }
    return true;
  };

  const handleNewSessionButton = () => {
    navigate("/app/data");
  };

  return (
    <SideBar>
      {/* Create new item button */}
      <Box p={4} sx={{ height: "64px", display: "flex", alignItems: "center" }}>
        {selectedDatasetId || selectedNotebookId ? (
          <NewItemButton
            onClick={handleNewSessionButton}
            title={t("datasets:button.datasetHub")}
            EndIcon={ViewModuleIcon}
          />
        ) : (
          <Typography variant="body1" color="textSecondary">
            {t("datasets:label.datasetModule")}
          </Typography>
        )}
      </Box>

      {/* Search bar global */}
      {totalItems > SEARCH_THRESHOLD && (
        <Box px={4} pb={4} flex={"0 0 auto"}>
          <SearchBar
            placeholder={t("datasets:label.searchDatasetsNotebooks")}
            value={searchQuery}
            onChange={handleSearchChange}
          />
        </Box>
      )}

      <Divider sx={{ width: "90%", bgcolor: "divider", mx: "auto" }} />

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
          onMoveDataset={moveDatasetToFolder}
          onCreateFolder={createFolder}
          onRenameFolder={renameFolder}
          onDeleteFolder={deleteFolderById}
          onBulkDelete={onBulkDatasetDelete}
          title={t("datasets:label.availableDatasets")}
          getItemDescription={getDatasetDescription}
          getDeleteConfirmationContent={getDatasetDeleteConfirmationContent}
          getDeleteConfirmationWarning={getDatasetDeleteConfirmationWarning}
        />

        {!isHub && (
          <>
            <Divider sx={{ width: "90%", bgcolor: "divider", mx: "auto" }} />

            <CollapsibleList
              items={filteredNotebooks}
              selectedItemId={selectedNotebookId}
              onItemClick={onNotebookClick}
              onItemDelete={onNotebookDelete}
              onItemEdit={editNotebook}
              onItemInfo={handleNotebookInfo}
              defaultOpen={true}
              collapsible={false}
              title={t("datasets:label.notebooks")}
              Icon={DescriptionIcon}
              datasets={datasets}
              getItemDescription={getNotebookDescription}
              getDeleteConfirmationContent={
                getNotebookDeleteConfirmationContent
              }
              onBulkDelete={onBulkNotebookDelete}
              selectItemsTooltip={t(
                "datasets:label.selectNotebooksToDelete",
                "Select notebooks to delete",
              )}
              getBulkDeleteConfirmationContent={
                getNotebookBulkDeleteConfirmationContent
              }
            />
          </>
        )}

        {isHub && (
          <>
            <Divider sx={{ width: "90%", bgcolor: "divider", mx: "auto" }} />

            <CollapsibleList
              items={filteredDownloads}
              selectedItemId={selectedDatafileId}
              onItemClick={(id) => {
                navigate(`/app/data/hub/import/${id}`);
              }}
              onItemDelete={handleDeleteDownload}
              defaultOpen={true}
              title={t("hub:downloadedDatasets")}
              Icon={CloudDownloadIcon}
              getItemDescription={(dl) =>
                t("hub:fromSource", { source: dl.source_name })
              }
            />
          </>
        )}
      </Box>

      {/* Footer */}
      <Footer />

      {/* Notebook Info Modal */}
      {selectedInfoNotebook && (
        <InfoNotebookModal
          notebookData={selectedInfoNotebook}
          datasets={datasets}
          open={!!selectedInfoNotebook}
          onClose={() => setSelectedInfoNotebook(null)}
        />
      )}
    </SideBar>
  );
}
