import { useEffect } from "react";
import { useLocation, useParams } from "react-router-dom";
import ModuleContainer from "../../components/layout/ModuleContainer";
import LeftPanel from "../../components/threeSectionLayout/panels/LeftPanel";
import DatasetsNotebooksLeftBar from "../../components/notebooks/DatasetNotebookLeftBar";
import CenterPanel from "../../components/threeSectionLayout/panels/CenterPanel";
import RightBar from "../../components/notebooks/RightBar";
import RightPanel from "../../components/threeSectionLayout/panels/RightPanel";
import DatasetsCenterContent from "../../components/notebooks/dataset/DatasetsCenterContent";
import { TourProvider } from "../../components/tour/TourProvider";
import { TOUR_KEYS } from "../../constants/tours";
import { ExplorersAndConvertersProvider } from "../../components/notebooks/context/ExplorersAndConvertersContext";
import { useThreePanelLayout } from "../../hooks/useThreePanelsLayout";
import { ThreePanelLayoutContext } from "../../components/threeSectionLayout/panels/ThreePanelLayoutContext";
import {
  OptionsEnum,
  useDatasetsAndNotebooks,
} from "../../components/custom/contexts/DatasetsAndNotebooksContext";
import { useTranslation } from "react-i18next";

export default function DatasetsContent() {
  const { t } = useTranslation();
  const threePanelLayout = useThreePanelLayout({ storageKey: "datasets" });
  const location = useLocation();
  const params = useParams();

  const {
    notebooks,
    selectedNotebookId,
    selectedDatasetId,
    selectedDocumentId,
    selectedOption,
    rightBarContent,
    step,
    selectDataset,
    selectNotebook,
    selectDocument,
    clearSelectedDataset,
    clearSelectedNotebook,
    clearSelectedDocument,
    setStep,
    setSelectedOption,
    setRightBarContent,
  } = useDatasetsAndNotebooks();

  useEffect(() => {
    const path = location.pathname;
    const clearSelection = () => {
      clearSelectedDataset();
      clearSelectedNotebook();
      clearSelectedDocument();
    };
    const openCreation = (option) => {
      clearSelection();
      setSelectedOption(option);
      setStep(1);
    };
    const openItem = (select, option) => {
      clearSelection();
      select(Number(params.id));
      setSelectedOption(option);
      setStep(0);
      setRightBarContent(null);
    };

    if (path.startsWith("/app/data/datasets/new")) {
      openCreation(OptionsEnum.DATASET);
      return;
    }
    if (path.startsWith("/app/data/documents/new")) {
      openCreation(OptionsEnum.DOCUMENT);
      return;
    }
    if (path.startsWith("/app/data/notebooks/new")) {
      openCreation(OptionsEnum.NOTEBOOK);
      return;
    }
    if (path.startsWith("/app/data/datasets/") && params.id) {
      openItem(selectDataset, OptionsEnum.DATASET);
      return;
    }
    if (path.startsWith("/app/data/documents/") && params.id) {
      openItem(selectDocument, OptionsEnum.DOCUMENT);
      return;
    }
    if (path.startsWith("/app/data/notebooks/") && params.id) {
      openItem(selectNotebook, OptionsEnum.NOTEBOOK);
      return;
    }

    clearSelection();
    setSelectedOption(OptionsEnum.NEW);
    setStep(0);
    setRightBarContent(null);
  }, [location.pathname, params.id]);

  const selectedNotebook = notebooks.find((n) => n.id === selectedNotebookId);

  return (
    <ThreePanelLayoutContext.Provider value={threePanelLayout}>
      <ModuleContainer>
        <LeftPanel>
          <DatasetsNotebooksLeftBar
            onToggle={threePanelLayout.handleToggleLeft}
          />
        </LeftPanel>

        <ExplorersAndConvertersProvider>
          {selectedDocumentId && selectedOption === OptionsEnum.DOCUMENT ? (
            <>
              <CenterPanel>
                <DatasetsCenterContent />
              </CenterPanel>
              <RightPanel toggleButtonTop="50%">{rightBarContent}</RightPanel>
            </>
          ) : selectedNotebookId ? (
            <TourProvider
              tourKey={TOUR_KEYS.NOTEBOOK}
              disabled={step !== 0}
              disabledMessage={t("datasets:label.tourDisabledMessage")}
            >
              <>
                <CenterPanel>
                  <DatasetsCenterContent />
                </CenterPanel>
                <RightPanel toggleButtonTop="50%">
                  {rightBarContent ? (
                    rightBarContent
                  ) : (
                    <RightBar
                      notebook={selectedNotebook}
                      onToggle={threePanelLayout.handleToggleRight}
                    />
                  )}
                </RightPanel>
              </>
            </TourProvider>
          ) : selectedDatasetId ||
            (step === 1 &&
              selectedOption === OptionsEnum.NOTEBOOK &&
              location.state?.preselectedDatasetId) ? (
            <TourProvider
              tourKey={TOUR_KEYS.DATASET_VIEW}
              disabled={step !== 0}
              disabledMessage={t("datasets:label.tourDisabledMessageNotebook")}
            >
              <>
                <CenterPanel>
                  <DatasetsCenterContent />
                </CenterPanel>
                <RightPanel toggleButtonTop="50%">
                  {rightBarContent ? (
                    rightBarContent
                  ) : (
                    <RightBar
                      notebook={null}
                      onToggle={threePanelLayout.handleToggleRight}
                    />
                  )}
                </RightPanel>
              </>
            </TourProvider>
          ) : (
            <TourProvider
              tourKey={TOUR_KEYS.DATASETS}
              disabled={step !== 0}
              disabledMessage={t("datasets:label.tourDisabledMessage")}
            >
              <>
                <CenterPanel>
                  <DatasetsCenterContent />
                </CenterPanel>
                <RightPanel toggleButtonTop="50%">
                  {rightBarContent ? (
                    rightBarContent
                  ) : (
                    <RightBar
                      notebook={null}
                      onToggle={threePanelLayout.handleToggleRight}
                    />
                  )}
                </RightPanel>
              </>
            </TourProvider>
          )}
        </ExplorersAndConvertersProvider>
      </ModuleContainer>
    </ThreePanelLayoutContext.Provider>
  );
}
