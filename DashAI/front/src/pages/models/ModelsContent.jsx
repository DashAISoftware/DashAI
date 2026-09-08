import { useEffect } from "react";
import { useLocation, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { TourProvider } from "../../components/tour/TourProvider";
import { TOUR_KEYS } from "../../constants/tours";
import ModuleContainer from "../../components/layout/ModuleContainer";
import LeftPanel from "../../components/threeSectionLayout/panels/LeftPanel";
import CenterPanel from "../../components/threeSectionLayout/panels/CenterPanel";
import RightPanel from "../../components/threeSectionLayout/panels/RightPanel";
import ModelsLeftBar from "../../components/models/ModelsLeftBar";
import ModelsRightBar from "../../components/models/ModelsRightBar";
import SessionVisualization from "../../components/models/SessionVisualization";
import ModelsCenterContent from "../../components/models/ModelCenterContent";
import { useThreePanelLayout } from "../../hooks/useThreePanelsLayout";
import { ThreePanelLayoutContext } from "../../components/threeSectionLayout/panels/ThreePanelLayoutContext";
import { useModels } from "../../components/models/ModelsContext";
import { getDatasetInfo } from "../../api/datasets";

export default function ModelsContent() {
  const location = useLocation();
  const params = useParams();
  const threePanelLayout = useThreePanelLayout({ storageKey: "models" });
  const { t } = useTranslation(["models"]);

  const {
    sessions,
    tasks,
    step,
    setStep,
    selectedSessionId,
    setSelectedSessionId,
    setSelectedSession,
    setSelectedTask,
    selectDataset,
    setRuns,
    fetchRuns,
    setActiveRunId,
    setDatasetRowCount,
  } = useModels();

  useEffect(() => {
    const path = location.pathname;

    if (path.startsWith("/app/models/datasets/") && params.id) {
      const id = Number(params.id);
      selectDataset(id);
      setSelectedSessionId(null);
      setSelectedTask(null);
      setActiveRunId(null);
      setStep(2);
      return;
    }

    if (
      path.startsWith("/app/models/sessions/new/") &&
      params.taskName &&
      tasks.length > 0
    ) {
      const task = tasks.find((tk) => tk.name === params.taskName);
      if (task) {
        setSelectedTask(task);
        setSelectedSessionId(null);
        setActiveRunId(null);
        setStep(1);
      }
      return;
    }

    if (path.startsWith("/app/models/sessions/") && params.id) {
      const id = Number(params.id);
      setSelectedSessionId(id);
      setActiveRunId(params.runId ? Number(params.runId) : null);
      selectDataset(null);
      return;
    }

    if (path === "/app/models" || path === "/app/models/") {
      setSelectedSessionId(null);
      setSelectedTask(null);
      setActiveRunId(null);
      const preserved = location.state?.preselectedDatasetId;
      if (preserved != null) {
        selectDataset(preserved);
      } else {
        selectDataset(null);
      }
      setStep(0);
    }
  }, [
    location.pathname,
    location.state?.preselectedDatasetId,
    params.id,
    params.taskName,
    params.runId,
    tasks,
  ]);

  useEffect(() => {
    if (location.state?.openSessionId && sessions.length > 0) {
      const sessionToOpen = sessions.find(
        (s) => s.id === location.state.openSessionId,
      );
      if (sessionToOpen) {
        setSelectedSessionId(sessionToOpen.id);
        setSelectedSession(sessionToOpen);
        setStep(2);
        window.history.replaceState({}, document.title);
      }
    }
  }, [location.state, sessions]);

  // Fetch runs when session is selected
  useEffect(() => {
    if (selectedSessionId) {
      fetchRuns();
    } else {
      setRuns([]);
      setSelectedSession(null);
    }
  }, [selectedSessionId, fetchRuns]);

  // Update selected session object when sessions or selectedSessionId changes
  useEffect(() => {
    if (selectedSessionId && sessions.length > 0) {
      const session = sessions.find((s) => s.id === selectedSessionId);
      setSelectedSession(session || null);
      //Update dataset row count when selected session changes
      if (session && session.dataset_id) {
        getDatasetInfo(Number(session.dataset_id)).then((info) => {
          setDatasetRowCount(info.total_rows);
        });
      }
    }
  }, [selectedSessionId, sessions]);

  return (
    <ThreePanelLayoutContext.Provider value={threePanelLayout}>
      <TourProvider
        tourKey={TOUR_KEYS.MODELS}
        disabled={step !== 0}
        disabledMessage={t("models:label.tourDisabledMessage")}
      >
        <ModuleContainer>
          {/* Left Panel */}
          <LeftPanel data-tour="models-left-panel">
            <ModelsLeftBar onToggle={threePanelLayout.handleToggleLeft} />
          </LeftPanel>
          {selectedSessionId ? (
            <TourProvider tourKey={TOUR_KEYS.MODELS_SESSION}>
              <CenterPanel data-tour="models-center-panel">
                <SessionVisualization />
              </CenterPanel>
              <RightPanel data-tour="models-right-panel" toggleButtonTop="50%">
                <ModelsRightBar onToggle={threePanelLayout.handleToggleRight} />
              </RightPanel>
            </TourProvider>
          ) : (
            <>
              <CenterPanel data-tour="models-center-panel">
                <ModelsCenterContent />
              </CenterPanel>

              {/* Right Panel */}
              <RightPanel data-tour="models-right-panel" toggleButtonTop="50%">
                <ModelsRightBar onToggle={threePanelLayout.handleToggleRight} />
              </RightPanel>
            </>
          )}
        </ModuleContainer>
      </TourProvider>
    </ThreePanelLayoutContext.Provider>
  );
}
