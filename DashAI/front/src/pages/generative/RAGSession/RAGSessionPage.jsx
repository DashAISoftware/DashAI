import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, CircularProgress, Divider, Typography } from "@mui/material";
import ModuleContainer from "../../../components/layout/ModuleContainer";
import LeftPanel from "../../../components/threeSectionLayout/panels/LeftPanel";
import CenterPanel from "../../../components/threeSectionLayout/panels/CenterPanel";
import RightPanel from "../../../components/threeSectionLayout/panels/RightPanel";
import SessionBar from "../../../components/generative/SessionBar";
import GenerativeHubHeader from "../../../components/generative/GenerativeHubHeader";
import GenerativeChat from "../../../components/generative/GenerativeChat";
import DocumentsBar from "../../../components/generative/RAG/DocumentsBar";
import RAGBreadcrumbs from "../../../components/generative/RAG/RAGBreadcrumbs";
import RAGConfigPanel from "../../../components/generative/RAG/RAGConfigPanel";
import { getGenerativeSession } from "../../../api/generativeTask";
import { getSessionIndexStatus, startSessionIndexing } from "../../../api/rag";
import { RAG_TASK_NAME } from "../../../api/rag";
import { useGenerative } from "../../../components/generative/GenerativeContext";
import { useTaskDisplayName } from "../../../hooks/generative/useTaskDisplayName";
import { useThreePanelLayout } from "../../../hooks/useThreePanelsLayout";
import { ThreePanelLayoutContext } from "../../../components/threeSectionLayout/panels/ThreePanelLayoutContext";
import { FormSchemaProvider } from "../../../contexts/schema";

/**
 * A RAG session: documents on the left, the chat in the centre, configuration
 * on the right.
 *
 * The chat is the default — and only — content of the centre column, so opening
 * a session lands straight in the conversation, and adjusting the retrieval or
 * the model never takes it off screen.
 *
 * @returns {JSX.Element} The three-panel RAG session page.
 */
export default function RAGSessionPage() {
  const navigate = useNavigate();
  const { id: urlSessionId } = useParams();
  const threePanelLayout = useThreePanelLayout({ storageKey: "rag" });
  const { t } = useTranslation(["generative"]);

  const {
    sessions,
    selectedSessionId,
    setSelectedSessionId,
    setSelectedTaskName,
    setSelectedDisplayName,
    deleteSessionById,
    fetchSessions,
  } = useGenerative();

  const ragTitle = useTaskDisplayName(RAG_TASK_NAME);

  const [notFound, setNotFound] = useState(false);
  const [indexStatus, setIndexStatus] = useState(null);
  const [sessionName, setSessionName] = useState(null);

  const sessionId = Number(urlSessionId);
  const isValidId = Number.isFinite(sessionId) && sessionId > 0;

  // Point the shared generative context at this session so the chat, which is
  // the same component every generative task uses, knows what it is talking to.
  useEffect(() => {
    if (!isValidId) {
      setNotFound(true);
      return;
    }
    let cancelled = false;
    setNotFound(false);
    getGenerativeSession(sessionId)
      .then((session) => {
        if (cancelled || !session) return;
        setSessionName(session.name ?? null);
        setSelectedSessionId?.(sessionId);
        setSelectedTaskName?.(session.task_name);
        setSelectedDisplayName?.(session.display_name ?? null);
      })
      .catch(() => {
        if (!cancelled) setNotFound(true);
      });
    return () => {
      cancelled = true;
    };
  }, [
    sessionId,
    isValidId,
    setSelectedSessionId,
    setSelectedTaskName,
    setSelectedDisplayName,
  ]);

  const refreshIndexStatus = useCallback(() => {
    if (!isValidId) return;
    getSessionIndexStatus(sessionId)
      .then(setIndexStatus)
      .catch((error) =>
        console.error("Failed to load RAG index status:", error),
      );
  }, [sessionId, isValidId]);

  useEffect(() => {
    refreshIndexStatus();
  }, [refreshIndexStatus]);

  // Indexing runs up front rather than on the first message, so every change
  // that could invalidate it ends here. The backend decides whether there is
  // actually anything to do, and answers with the resulting status.
  const startIndexing = useCallback(() => {
    if (!isValidId) return;
    startSessionIndexing(sessionId)
      .then(setIndexStatus)
      .catch((error) => {
        console.error("Failed to start RAG indexing:", error);
        // Fall back to reading the status: the user still needs to see where
        // the session stands, even if starting the run failed.
        refreshIndexStatus();
      });
  }, [sessionId, isValidId, refreshIndexStatus]);

  // Poll only while a job is actually running, so this stops on its own. The
  // status is recomputed against the queue on every call, which is what lets
  // it recover from a job that was cancelled or killed.
  useEffect(() => {
    if (indexStatus?.status !== "indexing") return undefined;
    const interval = setInterval(refreshIndexStatus, 1500);
    return () => clearInterval(interval);
  }, [indexStatus?.status, refreshIndexStatus]);

  const handleSessionClick = useCallback(
    (clickedId) => navigate(`/app/generative/rag/sessions/${clickedId}`),
    [navigate],
  );

  const handleSessionDelete = useCallback(
    async (deletedId) => {
      await deleteSessionById?.(deletedId);
      if (deletedId === sessionId) navigate("/app/generative/rag");
    },
    [deleteSessionById, navigate, sessionId],
  );

  const handleSessionRenamed = useCallback(
    (newName) => {
      // Keep the breadcrumb in step without waiting for a reload.
      if (newName) setSessionName(newName);
      fetchSessions?.();
    },
    [fetchSessions],
  );

  if (notFound) {
    return (
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        height="100vh"
      >
        <Typography variant="h6" color="text.secondary">
          {t("generative:rag.session.notFound")}
        </Typography>
      </Box>
    );
  }

  if (selectedSessionId !== sessionId) {
    return (
      <Box
        display="flex"
        alignItems="center"
        justifyContent="center"
        height="100vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <FormSchemaProvider>
      <ThreePanelLayoutContext.Provider value={threePanelLayout}>
        <ModuleContainer>
          <LeftPanel data-tour="sessions-left-panel">
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                minHeight: 0,
                bgcolor: "background.box",
              }}
            >
              {/* Above the split, so the way out of a session sits where it
                  does on every other screen in the module. */}
              <GenerativeHubHeader
                showHubButton
                onHubClick={() => navigate("/app/generative")}
              />
              <Divider />
              {/* Both halves may shrink, and each scrolls its own content:
                  a fixed basis with an outer scroll pushed the header out of
                  view as the lists grew. */}
              <Box sx={{ flex: "1 1 55%", minHeight: 0, display: "flex" }}>
                <DocumentsBar
                  sessionId={sessionId}
                  indexStatus={indexStatus}
                  onDocumentChange={startIndexing}
                  showSearch
                />
              </Box>
              <Divider />
              <Box sx={{ flex: "1 1 45%", minHeight: 0, display: "flex" }}>
                <SessionBar
                  sessions={sessions}
                  selectedSessionId={sessionId}
                  handleSessionClick={handleSessionClick}
                  handleSessionDelete={handleSessionDelete}
                  onToggle={threePanelLayout.handleToggleLeft}
                  showSearch={false}
                  showHeader={false}
                  title={ragTitle}
                />
              </Box>
            </Box>
          </LeftPanel>

          <CenterPanel>
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                minHeight: 0,
              }}
            >
              {/* Page chrome, level with the other RAG tabs. It used to be
                  rendered by the chat, which sits lower and is shared with
                  every other generative task. */}
              <Box sx={{ px: 4, pt: 4 }}>
                <RAGBreadcrumbs sessionName={sessionName} />
              </Box>
              <Box sx={{ flex: 1, minHeight: 0 }}>
                <GenerativeChat key={sessionId} indexStatus={indexStatus} />
              </Box>
            </Box>
          </CenterPanel>

          <RightPanel toggleButtonTop="50%" data-tour="parameters-right-panel">
            <RAGConfigPanel
              sessionId={sessionId}
              indexStatus={indexStatus}
              onSaved={startIndexing}
              onRetryIndexing={startIndexing}
              onSessionRenamed={handleSessionRenamed}
            />
          </RightPanel>
        </ModuleContainer>
      </ThreePanelLayoutContext.Provider>
    </FormSchemaProvider>
  );
}
