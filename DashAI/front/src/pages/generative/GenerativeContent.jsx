import { useEffect } from "react";
import { useLocation, useParams } from "react-router-dom";
import ModuleContainer from "../../components/layout/ModuleContainer";
import LeftPanel from "../../components/threeSectionLayout/panels/LeftPanel";
import CenterPanel from "../../components/threeSectionLayout/panels/CenterPanel";
import RightPanel from "../../components/threeSectionLayout/panels/RightPanel";
import SessionBar from "../../components/generative/SessionBar";
import GenerativeChat from "../../components/generative/GenerativeChat";
import ParamsBar from "../../components/generative/ParamsBar";
import CreateSessionLanding from "../../components/generative/CreateSessionLanding";
import CreateSessionCenter from "../../components/generative/CreateSessionCenter";
import CreateSessionRight from "../../components/generative/CreateSessionRight";
import { CreateSessionProvider } from "../../components/generative/CreateSessionContext";
import { useThreePanelLayout } from "../../hooks/useThreePanelsLayout";
import { ThreePanelLayoutContext } from "../../components/threeSectionLayout/panels/ThreePanelLayoutContext";
import { useTourContext } from "../../components/tour/TourProvider";
import { useGenerative } from "../../components/generative/GenerativeContext";
import { useTranslation } from "react-i18next";

export default function GenerativeContent() {
  const threePanelLayout = useThreePanelLayout({ storageKey: "generative" });
  const location = useLocation();
  const params = useParams();
  const {
    stepIndex,
    selectedSessionId,
    setSelectedSessionId,
    setSelectedTaskName,
    setSelectedDisplayName,
    setStepIndex,
    sessions,
    tasks,
  } = useGenerative();
  const tourContext = useTourContext();
  const { setDisabled } = tourContext ?? {};
  const { t } = useTranslation(["generative"]);

  const isCreating = location.pathname.startsWith(
    "/app/generative/sessions/new",
  );

  useEffect(() => {
    const path = location.pathname;

    if (isCreating) {
      setSelectedSessionId(null);
      setSelectedTaskName("");
      setSelectedDisplayName(null);
      setStepIndex(1);
      return;
    }

    if (path.startsWith("/app/generative/sessions/") && params.id) {
      if (sessions.length === 0 || tasks.length === 0) return;
      const id = Number(params.id);
      const session = sessions.find((s) => s.id === id);
      if (!session) return;
      const task = tasks.find((tk) => tk.name === session.task_name);
      setSelectedTaskName(session.task_name);
      setSelectedDisplayName(task?.display_name ?? null);
      setSelectedSessionId(id);
      setStepIndex(0);
      return;
    }

    if (path === "/app/generative" || path === "/app/generative/") {
      setSelectedSessionId(null);
      setSelectedTaskName("");
      setSelectedDisplayName(null);
      setStepIndex(0);
    }
  }, [location.pathname, params.id, tasks, sessions, isCreating]);

  useEffect(() => {
    setDisabled?.(
      stepIndex !== 0 || !!selectedSessionId,
      t("generative:label.tourDisabledMessage"),
    );
  }, [stepIndex, selectedSessionId, setDisabled, t]);

  useEffect(() => {
    if (!tourContext?.run || !selectedSessionId) return;
    const currentTarget = tourContext.steps?.[tourContext.stepIndex]?.target;
    if (currentTarget === '[data-tour="sessions-left-panel"]') {
      tourContext.resumeAtStep(tourContext.stepIndex);
    }
  }, [selectedSessionId]);

  const renderCenter = () => {
    if (selectedSessionId) return <GenerativeChat />;
    if (isCreating) return <CreateSessionCenter />;
    return <CreateSessionLanding />;
  };

  const renderRight = () => {
    if (isCreating) return <CreateSessionRight />;
    return <ParamsBar onToggle={threePanelLayout.handleToggleRight} />;
  };

  return (
    <CreateSessionProvider>
      <ThreePanelLayoutContext.Provider value={threePanelLayout}>
        <ModuleContainer>
          <LeftPanel data-tour="sessions-left-panel">
            <SessionBar onToggle={threePanelLayout.handleToggleLeft} />
          </LeftPanel>
          <CenterPanel>{renderCenter()}</CenterPanel>
          <RightPanel toggleButtonTop="50%" data-tour="parameters-right-panel">
            {renderRight()}
          </RightPanel>
        </ModuleContainer>
      </ThreePanelLayoutContext.Provider>
    </CreateSessionProvider>
  );
}
