import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Box, Typography } from "@mui/material";
import ModuleContainer from "../../../components/layout/ModuleContainer";
import LeftPanel from "../../../components/threeSectionLayout/panels/LeftPanel";
import CenterPanel from "../../../components/threeSectionLayout/panels/CenterPanel";
import RightPanel from "../../../components/threeSectionLayout/panels/RightPanel";
import SessionBar from "../../../components/generative/SessionBar";
import RAGBreadcrumbs from "../../../components/generative/RAG/RAGBreadcrumbs";
import RAGDocumentsPanel from "../../../components/generative/RAG/RAGDocumentsPanel";
import PromptSelectionTable from "../../../components/generative/RAG/PromptSelectionTable";
import { getSessions, removeSession } from "../../../api/session";
import { useThreePanelLayout } from "../../../hooks/useThreePanelsLayout";
import { ThreePanelLayoutContext } from "../../../components/threeSectionLayout/panels/ThreePanelLayoutContext";
import { FormSchemaProvider } from "../../../contexts/schema";

/**
 * RAG prompts management page.
 * Displays a prompt selection table in the center, sessions in the left panel,
 * and a document panel on the right.
 * @returns {JSX.Element} Three-panel prompts page.
 */
function RAGPromptsPage() {
  const navigate = useNavigate();
  const threePanelLayout = useThreePanelLayout();
  const { t } = useTranslation(["generative"]);
  const [rowSelectionModel, setRowSelectionModel] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [documentRefreshTrigger, setDocumentRefreshTrigger] = useState(0);

  /**
   * Fetch all sessions from the API.
   */
  const loadSessions = useCallback(async () => {
    try {
      const allSessions = await getSessions();
      setSessions(allSessions);
    } catch (error) {
      console.error("RAGPromptsPage: Error loading sessions:", error);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  /**
   * Navigate to the main generative page with the selected session pre-selected.
   * @param {number} sessionId
   * @param {string} taskName
   * @param {string} taskDisplayName
   */
  const handleSessionClick = (sessionId, taskName, taskDisplayName) => {
    navigate("/app/generative", {
      state: {
        selectedSessionId: sessionId,
        selectedTaskName: taskName,
        selectedDisplayName: taskDisplayName,
      },
    });
  };

  const handleNewSessionButton = () => {
    navigate("/app/generative");
  };

  /**
   * Remove a session optimistically and persist the deletion.
   * @param {number} id - Session id to delete.
   */
  const handleSessionDelete = async (id) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
    await removeSession(id);
  };

  const handleRowSelectionModelChange = (newSelection) => {
    setRowSelectionModel(newSelection);
  };

  const handleDocumentChange = () => {
    setDocumentRefreshTrigger((prev) => prev + 1);
  };

  return (
    <FormSchemaProvider>
      <ThreePanelLayoutContext.Provider value={threePanelLayout}>
        <ModuleContainer>
          <LeftPanel data-tour="sessions-left-panel">
            <SessionBar
              sessions={sessions}
              handleSessionClick={handleSessionClick}
              handleNewSessionButton={handleNewSessionButton}
              handleSessionDelete={handleSessionDelete}
              stepIndex={0}
              onToggle={threePanelLayout.handleToggleLeft}
              showSearch={false}
            />
          </LeftPanel>

          <CenterPanel data-tour="prompts-center-panel">
            <RAGBreadcrumbs />
            <Typography variant="h5" component="h1">
              {t("generative:ragPromptsPage.title")}
            </Typography>
            <Typography variant="subtitle1" component="p" sx={{ mb: 2 }}>
              {t("generative:ragPromptsPage.description")}
            </Typography>
            <PromptSelectionTable
              showTableTitle={false}
              loading={false}
              rowSelectionModel={rowSelectionModel}
              onRowSelectionModelChange={handleRowSelectionModelChange}
            />
          </CenterPanel>

          <RightPanel toggleButtonTop="50%" data-tour="documents-right-panel">
            <Box
              width="100%"
              height="100%"
              sx={{
                backgroundColor: "background.box",
                borderRadius: 2,
                minWidth: 0,
                maxWidth: "100%",
                overflow: "auto",
                p: 2,
              }}
            >
              <RAGDocumentsPanel
                selectedSessionId={null}
                isRagChatActive={false}
                onDocumentChange={handleDocumentChange}
              />
            </Box>
          </RightPanel>
        </ModuleContainer>
      </ThreePanelLayoutContext.Provider>
    </FormSchemaProvider>
  );
}

export default RAGPromptsPage;
