import { useCallback } from "react";
import { Box } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import ChatIcon from "@mui/icons-material/Chat";
import ModuleContainer from "../../../components/layout/ModuleContainer";
import LeftPanel from "../../../components/threeSectionLayout/panels/LeftPanel";
import CenterPanel from "../../../components/threeSectionLayout/panels/CenterPanel";
import SelectOptionMenu from "../../../components/threeSectionLayout/SelectOptionMenu";
import SessionBar from "../../../components/generative/SessionBar";
import RAGBreadcrumbs from "../../../components/generative/RAG/RAGBreadcrumbs";
import { RAG_TASK_NAME } from "../../../api/rag";
import { useGenerative } from "../../../components/generative/GenerativeContext";
import { useTaskDisplayName } from "../../../hooks/generative/useTaskDisplayName";
import { useThreePanelLayout } from "../../../hooks/useThreePanelsLayout";
import { ThreePanelLayoutContext } from "../../../components/threeSectionLayout/panels/ThreePanelLayoutContext";

const NEW_SESSION = "new_session";

const ROUTES = {
  [NEW_SESSION]: "/app/generative/rag/new",
};

/**
 * Home of the RAG entry point.
 *
 * Lists the RAG sessions on the left, and starting a new one in the centre.
 * Documents and prompts used to be listed here too; both now belong to a
 * session and are managed from inside it. Sessions are scoped to RAG by the
 * provider that wraps this route, so the shared generative session list stays
 * separate.
 *
 * @returns {JSX.Element} The RAG home page.
 */
export default function RAGHomePage() {
  const navigate = useNavigate();
  const { t } = useTranslation(["generative"]);
  const threePanelLayout = useThreePanelLayout({ storageKey: "rag" });
  const { sessions, deleteSessionById } = useGenerative();
  const ragTitle = useTaskDisplayName(RAG_TASK_NAME);

  const handleOption = useCallback(
    (name) => navigate(ROUTES[name] ?? ROUTES[NEW_SESSION]),
    [navigate],
  );

  const handleSessionClick = useCallback(
    (sessionId) => navigate(`/app/generative/rag/sessions/${sessionId}`),
    [navigate],
  );

  const options = [
    {
      name: NEW_SESSION,
      display_name: t("generative:rag.home.newSession"),
      description: t("generative:rag.home.newSessionDescription"),
      Icon: ChatIcon,
    },
  ];

  return (
    <ThreePanelLayoutContext.Provider value={threePanelLayout}>
      <ModuleContainer>
        <LeftPanel data-tour="sessions-left-panel">
          <SessionBar
            sessions={sessions}
            handleSessionClick={handleSessionClick}
            handleNewSessionButton={() => handleOption(NEW_SESSION)}
            handleSessionDelete={deleteSessionById}
            onToggle={threePanelLayout.handleToggleLeft}
            showSearch={false}
            title={ragTitle}
          />
        </LeftPanel>

        <CenterPanel>
          <Box sx={{ px: 4, pt: 4 }}>
            <RAGBreadcrumbs />
          </Box>
          <SelectOptionMenu
            goToNextStep={handleOption}
            title={t("generative:rag.home.title")}
            subtitle={t("generative:rag.home.subtitle")}
            options={options}
            searchBar={false}
          />
        </CenterPanel>
      </ModuleContainer>
    </ThreePanelLayoutContext.Provider>
  );
}
