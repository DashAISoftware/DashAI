import { useState, useCallback, useEffect } from "react";
import { useSnackbar } from "notistack";
import {
  getDataset,
  getDatasets,
  deleteDataset,
  deleteDatasets as deleteDatasetsRequest,
  updateDataset,
  createDataset,
} from "../../api/datasets";
import { startJobPolling, subscribeJobs } from "../../utils/jobPoller";

export function useDatasets({ t }) {
  const { enqueueSnackbar } = useSnackbar();
  const [datasets, setDatasets] = useState([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState(null);
  const [datasetRowCount, setDatasetRowCount] = useState(null);

  useEffect(() => {
    fetchDatasets();
  }, []);

  // ---------------- actions ----------------

  const fetchDatasets = useCallback(async () => {
    const data = await getDatasets();
    setDatasets(data);
    return data;
  }, []);

  useEffect(() => {
    const unsubscribe = subscribeJobs((jobs) => {
      const finishedDatasetJobs = Array.isArray(jobs)
        ? jobs.filter(
            (job) =>
              job.task_type === "DatasetJob" && job.status === "finished",
          )
        : [];
      if (finishedDatasetJobs.length > 0) {
        fetchDatasets();
      }
    });

    return unsubscribe;
  }, [fetchDatasets]);

  const selectDataset = (id) => {
    setSelectedDatasetId(id);
  };

  const clearSelectedDataset = () => {
    setSelectedDatasetId(null);
  };

  const deleteDatasetById = async (id) => {
    try {
      await deleteDataset(id);
      setDatasets((prev) => prev.filter((d) => d.id !== id));
      if (id === selectedDatasetId) {
        setSelectedDatasetId(null);
      }
      return true;
    } catch (error) {
      enqueueSnackbar(t("datasets:error.failedToDeleteDataset"), {
        variant: "error",
      });
      console.error("Error deleting dataset:", error);
    }
    return false;
  };

  const deleteDatasetsByIds = async (ids) => {
    try {
      await deleteDatasetsRequest(ids);
      const idSet = new Set(ids);
      setDatasets((prev) => prev.filter((d) => !idSet.has(d.id)));
      if (idSet.has(selectedDatasetId)) {
        setSelectedDatasetId(null);
      }
      return true;
    } catch (error) {
      enqueueSnackbar(t("datasets:error.failedToDeleteDatasets"), {
        variant: "error",
      });
      console.error("Error deleting datasets:", error);
    }
    return false;
  };

  const editDataset = async (id, newName) => {
    try {
      const updated = await updateDataset(id, { name: newName });
      setDatasets((prev) =>
        prev.map((d) => (d.id === id ? { ...d, name: updated.name } : d)),
      );
      enqueueSnackbar(t("datasets:message.datasetUpdateSuccess"), {
        variant: "success",
      });
    } catch (error) {
      if (error.response?.status === 409) {
        enqueueSnackbar(t("datasets:error.datasetNameExists"), {
          variant: "error",
        });
      } else if (error.response?.status === 422) {
        enqueueSnackbar(t("datasets:error.datasetNameEmpty"), {
          variant: "error",
        });
      } else {
        enqueueSnackbar(t("datasets:error.failedToUpdateDataset"), {
          variant: "error",
        });
      }
      throw error;
    }
  };

  const addDatasetOptimistically = (dataset) => {
    setDatasets((prev) => [...prev, dataset]);
    setSelectedDatasetId(dataset.id);
  };

  const startDatasetPolling = (newDataset, datasetJob) => {
    startJobPolling(
      datasetJob.id,
      async () => {
        enqueueSnackbar(
          t("datasets:message.datasetCreationSuccess", {
            datasetName: newDataset.name,
          }),
          { variant: "success" },
        );
        setSelectedDatasetId(newDataset.id);
      },
      async () => {
        // The poller can fire onError when a job finishes too quickly to be
        // observed in the changes stream. Verify the dataset actually failed
        // before showing the error / removing the optimistic entry.
        try {
          const persisted = await getDataset(newDataset.id);
          if (persisted && persisted.status === "finished") {
            enqueueSnackbar(
              t("datasets:message.datasetCreationSuccess", {
                datasetName: newDataset.name,
              }),
              { variant: "success" },
            );
            setSelectedDatasetId(newDataset.id);
            return;
          }
        } catch (e) {
          console.error("Failed to verify dataset state after poll error:", e);
        }
        enqueueSnackbar(t("datasets:error.failedToCreateDataset"), {
          variant: "error",
        });
        setDatasets((prev) => prev.filter((d) => d.id !== newDataset.id));
      },
    );
  };

  const moveDatasetToFolder = async (id, folderId) => {
    const prevFolderId = datasets.find((d) => d.id === id)?.folder_id ?? null;
    setDatasets((prev) =>
      prev.map((d) => (d.id === id ? { ...d, folder_id: folderId } : d)),
    );
    try {
      await updateDataset(id, { folder_id: folderId });
    } catch (error) {
      setDatasets((prev) =>
        prev.map((d) =>
          d.id === id && (d.folder_id ?? null) === folderId
            ? { ...d, folder_id: prevFolderId }
            : d,
        ),
      );
      enqueueSnackbar(t("datasets:error.failedToMoveDataset"), {
        variant: "error",
      });
    }
  };

  const replaceDatasets = (datasets) => {
    setDatasets(datasets);
  };

  return {
    datasets,
    selectedDatasetId,
    createDataset,
    fetchDatasets,
    selectDataset,
    clearSelectedDataset,
    deleteDataset,
    deleteDatasetById,
    deleteDatasetsByIds,
    editDataset,
    moveDatasetToFolder,
    addDatasetOptimistically,
    startDatasetPolling,
    replaceDatasets,
    datasetRowCount,
    setDatasetRowCount,
  };
}
