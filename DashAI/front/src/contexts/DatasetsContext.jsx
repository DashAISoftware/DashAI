import {
  createContext,
  useContext,
  useCallback,
  useMemo,
  useState,
} from "react";
import { useTranslation } from "react-i18next";
import { useDatasets } from "../hooks/datasets/useDatasets";
import { useFolders } from "../hooks/datasets/useFolders";

const DatasetsContext = createContext(null);

export const useSharedDatasets = () => useContext(DatasetsContext);

export function DatasetsProvider({ children }) {
  const { t } = useTranslation(["datasets", "common"]);

  const {
    datasets,
    createDataset,
    selectedDatasetId,
    fetchDatasets,
    selectDataset,
    clearSelectedDataset,
    deleteDataset,
    deleteDatasetById,
    deleteDatasetsByIds,
    editDataset,
    addDatasetOptimistically,
    replaceDatasets,
    startDatasetPolling,
    moveDatasetToFolder,
  } = useDatasets({ t });

  const {
    folders,
    fetchFolders,
    createFolder,
    renameFolder,
    deleteFolderById: deleteFolderByIdRaw,
  } = useFolders({ t });

  // Which named folders are open/closed in the sidebar. Shared here (not in
  // ModelsContext/DatasetsAndNotebooksContext individually) so the Datasets
  // and Models modules — which each render their own DatasetFolderList
  // instance — show the same open/closed state instead of two independent
  // copies. A folder id with no entry here defaults to open (see
  // DatasetFolderList's read side).
  const [openFolderIds, setOpenFolderIds] = useState({});

  // Deleting a folder moves its datasets to "no folder" server-side
  // (folder_id set to null via the FK's ON DELETE SET NULL), but the local
  // `datasets` state still holds the old folder_id until this clears it —
  // otherwise those datasets vanish from the list until a full refetch.
  const deleteFolderById = useCallback(
    async (id) => {
      const success = await deleteFolderByIdRaw(id);
      if (success) {
        replaceDatasets((prev) =>
          prev.map((d) => (d.folder_id === id ? { ...d, folder_id: null } : d)),
        );
        setOpenFolderIds((prev) => {
          const { [id]: _removed, ...rest } = prev;
          return rest;
        });
      }
      return success;
    },
    [deleteFolderByIdRaw, replaceDatasets],
  );

  const value = useMemo(
    () => ({
      datasets,
      createDataset,
      selectedDatasetId,
      fetchDatasets,
      selectDataset,
      clearSelectedDataset,
      deleteDataset,
      deleteDatasetById,
      deleteDatasetsByIds,
      editDataset,
      addDatasetOptimistically,
      replaceDatasets,
      startDatasetPolling,
      moveDatasetToFolder,
      folders,
      fetchFolders,
      createFolder,
      renameFolder,
      deleteFolderById,
      openFolderIds,
      setOpenFolderIds,
    }),
    [
      datasets,
      createDataset,
      selectedDatasetId,
      fetchDatasets,
      selectDataset,
      clearSelectedDataset,
      deleteDataset,
      deleteDatasetById,
      deleteDatasetsByIds,
      editDataset,
      addDatasetOptimistically,
      replaceDatasets,
      startDatasetPolling,
      moveDatasetToFolder,
      folders,
      fetchFolders,
      createFolder,
      renameFolder,
      deleteFolderById,
      openFolderIds,
    ],
  );

  return (
    <DatasetsContext.Provider value={value}>
      {children}
    </DatasetsContext.Provider>
  );
}
