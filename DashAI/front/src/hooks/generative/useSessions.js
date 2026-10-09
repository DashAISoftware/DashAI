import { useState, useCallback } from "react";
import { useSnackbar } from "notistack";
import {
  getSessions,
  removeSession,
  removeSessions,
  updateGenerativeSession,
} from "../../api/session";
import { getComponents } from "../../api/component";

/**
 * Session list state for a generative module view.
 *
 * @param {object} params
 * @param {Function} params.t - i18next translator.
 * @param {object} [params.sessionFilter] - Narrows which sessions this view
 *   owns, e.g. `{ taskName: "RAGTask" }` to scope a task's own views to it.
 *   Unset lists every session. The backend applies the filter, so no session is
 *   ever filtered out client-side.
 */
export function useSessions({ t, sessionFilter }) {
  const { enqueueSnackbar } = useSnackbar();
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [tasks, setTasks] = useState([]);
  // TODO: Combine selectedTaskName and selectedDisplayName into a single selectedTask State
  const [selectedTaskName, setSelectedTaskName] = useState("");
  const [selectedDisplayName, setSelectedDisplayName] = useState("");
  const [sessions, setSessions] = useState([]);
  const [paramsVersion, setParamsVersion] = useState(0);

  // -------- actions --------

  // Fetch sessions on mount
  const filterKey = JSON.stringify(sessionFilter ?? null);
  const fetchSessions = useCallback(async () => {
    try {
      const data = await getSessions(sessionFilter);
      setSessions(data);
    } catch (error) {
      enqueueSnackbar(t("generative:error.failedToFetchSessions"), {
        variant: "error",
      });
      console.error("Failed to fetch sessions:", error);
    }
    // filterKey rather than sessionFilter: an inline object literal would be a
    // new reference on every render and refetch in a loop.
  }, [enqueueSnackbar, t, filterKey]);

  const fetchTasks = useCallback(async () => {
    try {
      const data = await getComponents({ selectTypes: "GenerativeTask" });
      setTasks(data);
    } catch (error) {
      enqueueSnackbar(t("generative:error.failedToFetchTasks"), {
        variant: "error",
      });
      console.error("Failed to fetch generative tasks:", error);
    }
  }, [enqueueSnackbar, t]);

  const deleteSessionById = async (id) => {
    try {
      await removeSession(id);

      if (id === selectedSessionId) {
        setSelectedSessionId(null);
      }

      setSessions((prev) => prev.filter((s) => s.id !== id));

      enqueueSnackbar(t("generative:message.sessionDeleted"), {
        variant: "success",
      });

      return true;
    } catch (error) {
      enqueueSnackbar(t("generative:error.failedToDeleteSession"), {
        variant: "error",
      });
      console.error("Error deleting session:", error);
    }
    return false;
  };

  const deleteSessionsByIds = async (ids) => {
    try {
      await removeSessions(ids);

      const idSet = new Set(ids);
      if (idSet.has(selectedSessionId)) {
        setSelectedSessionId(null);
      }

      setSessions((prev) => prev.filter((s) => !idSet.has(s.id)));

      return true;
    } catch (error) {
      enqueueSnackbar(t("generative:error.failedToDeleteSessions"), {
        variant: "error",
      });
      console.error("Error deleting sessions:", error);
    }
    return false;
  };

  const editSession = async (sessionId, newName) => {
    try {
      const result = await updateGenerativeSession({
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
      enqueueSnackbar(t("generative:message.sessionUpdated"), {
        variant: "success",
      });
    } catch (error) {
      console.error("Failed to update session:", error);
      if (error.response?.status === 409) {
        enqueueSnackbar(t("generative:error.sessionNameExists"), {
          variant: "error",
        });
      } else if (error.response?.status === 422) {
        enqueueSnackbar(t("generative:error.sessionNameEmpty"), {
          variant: "error",
        });
      } else {
        enqueueSnackbar(t("generative:error.failedToUpdateSession"), {
          variant: "error",
        });
      }
      throw error;
    }
  };

  return {
    selectedSessionId,
    setSelectedSessionId,
    tasks,
    setTasks,
    selectedTaskName,
    setSelectedTaskName,
    selectedDisplayName,
    setSelectedDisplayName,
    sessions,
    setSessions,
    paramsVersion,
    setParamsVersion,
    fetchSessions,
    fetchTasks,
    deleteSessionById,
    deleteSessionsByIds,
    editSession,
  };
}
