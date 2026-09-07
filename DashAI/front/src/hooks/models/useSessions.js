import { useState, useCallback } from "react";
import { useSnackbar } from "notistack";
import {
  getModelSessions,
  updateModelSession,
  deleteModelSession,
  deleteModelSessions,
} from "../../api/modelSession";
import { getComponents } from "../../api/component";
import {
  getRuns,
  deleteRun,
  resetRunById,
  getRunById,
  getRunOperationsCount,
  deleteRunOperations,
} from "../../api/run";

import { enqueueRunnerJob as enqueueRunnerJobRequest } from "../../api/job";
import { startJobPolling } from "../../utils/jobPoller";

export function useSessions({ t }) {
  const { enqueueSnackbar } = useSnackbar();
  const [tasks, setTasks] = useState([]);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [runs, setRuns] = useState([]);
  const [retrainDialogOpen, setRetrainDialogOpen] = useState(false);
  const [runToRetrain, setRunToRetrain] = useState(null);
  const [operationsCount, setOperationsCount] = useState(null);
  const [lastAddedRunId, setLastAddedRunId] = useState(null);

  // -------- actions --------

  const fetchSessions = useCallback(async () => {
    try {
      const data = await getModelSessions();
      setSessions(data);
    } catch (error) {
      enqueueSnackbar(t("models:error.failedToFetchSessions"), {
        variant: "error",
      });
      console.error("Failed to fetch sessions:", error);
    }
  }, [enqueueSnackbar, t]);

  const fetchTasks = useCallback(async () => {
    setLoadingTasks(true);
    try {
      const data = await getComponents({
        selectTypes: ["Task"],
        hasRelatedOfType: "Model",
      });
      setTasks(data);
    } catch (error) {
      enqueueSnackbar(t("models:error.failedToFetchTasks"), {
        variant: "error",
      });
      console.error("Failed to fetch tasks:", error);
    } finally {
      setLoadingTasks(false);
    }
  }, [enqueueSnackbar, t]);

  const editSession = async (sessionId, newName) => {
    try {
      const result = await updateModelSession({
        id: sessionId,
        formData: { name: newName },
      });
      setSessions((prev) =>
        prev.map((session) =>
          session.id === sessionId
            ? { ...session, name: result.name }
            : session,
        ),
      );
      enqueueSnackbar(t("models:message.sessionUpdated"), {
        variant: "success",
      });
    } catch (error) {
      console.error("Failed to update session:", error);
      if (error.response?.status === 409) {
        enqueueSnackbar(t("models:error.sessionNameExists"), {
          variant: "error",
        });
      } else if (error.response?.status === 422) {
        enqueueSnackbar(t("models:error.sessionNameEmpty"), {
          variant: "error",
        });
      } else {
        enqueueSnackbar(t("models:error.failedToUpdateSession"), {
          variant: "error",
        });
      }
      throw error;
    }
  };

  const deleteSessionById = async (id) => {
    try {
      await deleteModelSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      return true;
    } catch (error) {
      enqueueSnackbar(t("models:error.failedToDeleteSession"), {
        variant: "error",
      });
      console.error("Error deleting session:", error);
    }
    return false;
  };

  const deleteSessionsByIds = async (ids) => {
    try {
      await deleteModelSessions(ids);
      const idSet = new Set(ids);
      setSessions((prev) => prev.filter((s) => !idSet.has(s.id)));
      return true;
    } catch (error) {
      enqueueSnackbar(t("models:error.failedToDeleteSessions"), {
        variant: "error",
      });
      console.error("Error deleting sessions:", error);
    }
    return false;
  };

  const fetchRuns = useCallback(async () => {
    if (!selectedSessionId) return;
    try {
      const data = await getRuns(selectedSessionId.toString());

      setRuns(data);
    } catch (error) {
      enqueueSnackbar(t("models:error.failedToFetchRuns"), {
        variant: "error",
      });
      console.error("Failed to fetch runs:", error);
    }
  }, [selectedSessionId, enqueueSnackbar]);

  const executeTraining = async (run) => {
    try {
      // Always silently delete any existing operations before training
      const opsCount = await getRunOperationsCount(run.id.toString());
      if (opsCount.explainers > 0 || opsCount.predictions > 0) {
        await deleteRunOperations(run.id.toString());
      }

      const updatedRun = await resetRunById(run.id.toString());

      const response = await enqueueRunnerJobRequest(run.id);

      if (!response || !response.id) {
        enqueueSnackbar(
          t("models:error.failedToStartRun", { runName: run.name }),
          {
            variant: "error",
          },
        );
        return;
      }

      enqueueSnackbar(t("models:message.runStarted", { runName: run.name }), {
        variant: "success",
      });

      setRuns((prevRuns) =>
        prevRuns.map((r) =>
          r.id === run.id ? { ...updatedRun, status: 1 } : r,
        ),
      );

      startJobPolling(
        response.id,
        async () => {
          const updated = await getRunById(run.id.toString());
          setRuns((prevRuns) =>
            prevRuns.map((r) => (r.id === run.id ? updated : r)),
          );
          enqueueSnackbar(
            t("models:message.runCompleted", { runName: run.name }),
            {
              variant: "success",
            },
          );
        },
        async (result) => {
          const updated = await getRunById(run.id.toString());
          setRuns((prevRuns) =>
            prevRuns.map((r) => (r.id === run.id ? updated : r)),
          );
          enqueueSnackbar(
            t("models:error.runFailed", {
              runName: run.name,
              error: result.error || t("common:unknownError"),
            }),
            { variant: "error" },
          );
        },
      );

      setRetrainDialogOpen(false);
      setRunToRetrain(null);
      setOperationsCount(null);
    } catch (error) {
      console.error("Error training run:", error);
      enqueueSnackbar(
        t("models:error.failedToStartRun", { runName: run.name }),
        {
          variant: "error",
        },
      );
    }
  };

  const onRunCreated = (newRun) => {
    setRuns((prev) => [...prev, newRun]);
    setLastAddedRunId(newRun.id);
    enqueueSnackbar(t("models:message.runAdded", { runName: newRun.name }), {
      variant: "success",
    });
  };

  const clearLastAddedRunId = useCallback(() => setLastAddedRunId(null), []);

  const onTrainRun = async (run) => {
    try {
      // Only show confirmation dialog for previously trained runs (Retrain flow)
      const hasBeenTrained =
        run.test_metrics ||
        run.train_metrics ||
        run.validation_metrics ||
        run.status === 3; // Finished

      if (hasBeenTrained) {
        const opsCount = await getRunOperationsCount(run.id.toString());
        const hasOperations =
          opsCount.explainers > 0 || opsCount.predictions > 0;

        if (hasOperations) {
          setRunToRetrain(run);
          setOperationsCount(opsCount);
          setRetrainDialogOpen(true);
          return;
        }
      }

      await executeTraining(run);
    } catch (error) {
      console.error("Error checking operations:", error);
      // If check fails, proceed with training anyway
      await executeTraining(run);
    }
  };

  const onEditRun = async (run) => {
    enqueueSnackbar("Edit functionality coming soon", { variant: "info" });
  };

  const onDeleteRun = async (run) => {
    try {
      await deleteRun(run.id.toString());
      setRuns((prev) => prev.filter((r) => r.id !== run.id));
      enqueueSnackbar(t("models:message.runDeleted", { runName: run.name }), {
        variant: "success",
      });
    } catch (error) {
      console.error("Error deleting run:", error);
      enqueueSnackbar(
        t("models:error.failedToDeleteRun", { runName: run.name }),
        {
          variant: "error",
        },
      );
    }
  };

  const handleConfirmRetrain = () => {
    if (runToRetrain) {
      executeTraining(runToRetrain);
    }
  };

  const handleCancelRetrain = () => {
    setRetrainDialogOpen(false);
    setRunToRetrain(null);
    setOperationsCount(null);
  };

  return {
    tasks,
    loadingTasks,
    setTasks,
    selectedTask,
    setSelectedTask,
    selectedSessionId,
    setSelectedSessionId,
    selectedSession,
    setSelectedSession,
    sessions,
    setSessions,
    fetchSessions,
    fetchTasks,
    editSession,
    deleteSessionById,
    deleteSessionsByIds,
    runs,
    setRuns,
    retrainDialogOpen,
    setRetrainDialogOpen,
    runToRetrain,
    setRunToRetrain,
    operationsCount,
    setOperationsCount,
    fetchRuns,
    executeTraining,
    onRunCreated,
    onTrainRun,
    onEditRun,
    onDeleteRun,
    handleCancelRetrain,
    handleConfirmRetrain,
    lastAddedRunId,
    clearLastAddedRunId,
  };
}
