import { useCallback, useEffect, useState } from "react";
import { useSnackbar } from "notistack";
import {
  deleteDocument,
  getDocument,
  getDocuments,
  updateDocument,
} from "../../api/documents";
import {
  startJobPolling,
  subscribeJobs,
  TERMINAL_JOB_STATUSES,
} from "../../utils/jobPoller";

export const DOCUMENT_STATUS = Object.freeze({
  NOT_STARTED: 0,
  DELIVERED: 1,
  STARTED: 2,
  FINISHED: 3,
  ERROR: 4,
});

export function useDocuments({ t }) {
  const { enqueueSnackbar } = useSnackbar();
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await getDocuments();
      setDocuments(data);
      return data;
    } catch (error) {
      console.error("Error fetching documents:", error);
      return [];
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    const unsubscribe = subscribeJobs((jobs) => {
      const finished =
        Array.isArray(jobs) &&
        jobs.some(
          (job) =>
            job.task_type === "DocumentJob" &&
            TERMINAL_JOB_STATUSES.includes(job.status),
        );
      if (finished) fetchDocuments();
    });
    return unsubscribe;
  }, [fetchDocuments]);

  const selectDocument = useCallback((id) => setSelectedDocumentId(id), []);
  const clearSelectedDocument = useCallback(
    () => setSelectedDocumentId(null),
    [],
  );

  const refreshDocument = async (id) => {
    try {
      const fresh = await getDocument(id);
      setDocuments((prev) => prev.map((d) => (d.id === id ? fresh : d)));
      return fresh;
    } catch (error) {
      return null;
    }
  };

  const deleteDocumentById = async (id) => {
    try {
      await deleteDocument(id);
    } catch (error) {
      if (error.response?.status !== 404) {
        const key =
          error.response?.status === 409
            ? "datasets:document.deleteWhileParsing"
            : "datasets:document.failedToDelete";
        enqueueSnackbar(t(key), { variant: "error" });
        return false;
      }
    }
    setDocuments((prev) => prev.filter((d) => d.id !== id));
    setSelectedDocumentId((prev) => (prev === id ? null : prev));
    return true;
  };

  const editDocument = async (id, newName) => {
    try {
      const updated = await updateDocument(id, { name: newName });
      setDocuments((prev) =>
        prev.map((d) => (d.id === id ? { ...d, name: updated.name } : d)),
      );
    } catch (error) {
      const key =
        error.response?.status === 409
          ? "datasets:document.nameExists"
          : "datasets:document.failedToUpdate";
      enqueueSnackbar(t(key), { variant: "error" });
      throw error;
    }
  };

  const moveDocumentToFolder = async (id, folderId) => {
    const previous = documents.find((d) => d.id === id);
    setDocuments((prev) =>
      prev.map((d) => (d.id === id ? { ...d, folder_id: folderId } : d)),
    );
    try {
      await updateDocument(id, { folder_id: folderId });
    } catch (error) {
      setDocuments((prev) =>
        prev.map((d) =>
          d.id === id ? { ...d, folder_id: previous?.folder_id ?? null } : d,
        ),
      );
      enqueueSnackbar(t("datasets:document.failedToUpdate"), {
        variant: "error",
      });
    }
  };

  const addDocumentOptimistically = (document) => {
    setDocuments((prev) => [...prev, document]);
    setSelectedDocumentId(document.id);
  };

  const notifyReady = (name) =>
    enqueueSnackbar(t("datasets:document.creationSuccess", { name }), {
      variant: "success",
    });

  const startDocumentPolling = (newDocument, job) => {
    startJobPolling(
      job.id,
      async () => {
        await refreshDocument(newDocument.id);
        notifyReady(newDocument.name);
      },
      async (result) => {
        const fresh = await refreshDocument(newDocument.id);
        if (fresh?.status === DOCUMENT_STATUS.FINISHED) {
          notifyReady(newDocument.name);
          return;
        }
        if (result?.status === "cancelled") {
          enqueueSnackbar(t("common:jobQueue.jobCancelled"), {
            variant: "info",
          });
        } else {
          enqueueSnackbar(t("datasets:document.creationError"), {
            variant: "error",
          });
        }
      },
    );
  };

  return {
    documents,
    selectedDocumentId,
    fetchDocuments,
    selectDocument,
    clearSelectedDocument,
    deleteDocumentById,
    editDocument,
    moveDocumentToFolder,
    addDocumentOptimistically,
    startDocumentPolling,
    refreshDocument,
  };
}
