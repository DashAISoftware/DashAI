import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, CircularProgress, Typography } from "@mui/material";
import ModuleContainer from "../../../components/layout/ModuleContainer";
import LeftPanel from "../../../components/threeSectionLayout/panels/LeftPanel";
import CenterPanel from "../../../components/threeSectionLayout/panels/CenterPanel";
import RightPanel from "../../../components/threeSectionLayout/panels/RightPanel";
import SessionBar from "../../../components/generative/SessionBar";
import GenerativeChat from "../../../components/generative/GenerativeChat";
import RAGDocumentsPanel from "../../../components/generative/RAG/RAGDocumentsPanel";
import RAGConfigPanel from "../../../components/generative/RAG/RAGConfigPanel";
import { getGenerativeSession } from "../../../api/generativeTask";
import { getSessionIndexStatus } from "../../../api/rag";
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

  const handleSessionRenamed = useCallback(() => {
    fetchSessions?.();
  }, [fetchSessions]);

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
                gap: 1,
              }}
            >
              <Box sx={{ flex: "0 0 60%", minHeight: 0 }}>
                <RAGDocumentsPanel
                  selectedSessionId={sessionId}
                  indexStatus={indexStatus}
                  onDocumentChange={refreshIndexStatus}
                />
              </Box>
              <Box sx={{ flex: "0 0 40%", overflow: "auto", minHeight: 0 }}>
                <SessionBar
                  sessions={sessions}
                  selectedSessionId={sessionId}
                  handleSessionClick={handleSessionClick}
                  handleNewSessionButton={() =>
                    navigate("/app/generative/rag/new")
                  }
                  handleSessionDelete={handleSessionDelete}
                  onToggle={threePanelLayout.handleToggleLeft}
                  showSearch={false}
                  title={ragTitle}
                />
              </Box>
            </Box>
          </LeftPanel>

          <CenterPanel>
            <GenerativeChat key={sessionId} indexStatus={indexStatus} />
          </CenterPanel>

          <RightPanel toggleButtonTop="50%" data-tour="parameters-right-panel">
            <RAGConfigPanel
              sessionId={sessionId}
              indexStatus={indexStatus}
              onSaved={refreshIndexStatus}
              onSessionRenamed={handleSessionRenamed}
            />
          </RightPanel>
        </ModuleContainer>
      </ThreePanelLayoutContext.Provider>
    </FormSchemaProvider>
  );
}
