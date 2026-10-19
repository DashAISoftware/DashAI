import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Box, Typography } from "@mui/material";
import ModuleContainer from "../../components/layout/ModuleContainer";
import LeftPanel from "../../components/threeSectionLayout/panels/LeftPanel";
import CenterPanel from "../../components/threeSectionLayout/panels/CenterPanel";
import RightPanel from "../../components/threeSectionLayout/panels/RightPanel";
import { ThreePanelLayoutContext } from "../../components/threeSectionLayout/panels/ThreePanelLayoutContext";
import { useThreePanelLayout } from "../../hooks/useThreePanelsLayout";
import HubBreadcrumbs from "../../components/hub/HubBreadcrumbs";
import ComponentSelector from "../../components/custom/ComponentSelector";
import ComponentDetailsPanel from "../../components/custom/ComponentDetailsPanel";
import StepperNavigationFooter from "../../components/shared/StepperNavigationFooter";
import DatasetsNotebooksLeftBar from "../../components/notebooks/DatasetNotebookLeftBar";
import DatasetGrid from "../../components/hub/DatasetGrid";
import DatasetDetail from "../../components/hub/DatasetDetail";
import { createDatafile, getDatafile } from "../../api/hub";

import { getComponents } from "../../api/component";
import { enqueueDatafileJob } from "../../api/job";
import { startJobPolling } from "../../hooks/useJobPolling";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { useDatasetsAndNotebooks } from "../../components/custom/contexts/DatasetsAndNotebooksContext";
import {
  TourProvider,
  useTourContext,
} from "../../components/tour/TourProvider";
import {
  goToTourTarget,
  isTourAtTarget,
  useTourStageSync,
} from "../../components/tour/tourUtils";
import { TOUR_KEYS } from "../../constants/tours";

// Source the hub tour walks the user through (public, no credentials).
const TOUR_SOURCE = "HuggingFaceDatasetSource";

export default function HubContent() {
  return (
    <TourProvider tourKey={TOUR_KEYS.HUB}>
      <HubContentInner />
    </TourProvider>
  );
}

function HubContentInner() {
  const { t } = useTranslation(["hub"]);
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const {
    addDownload,
    updateDownload,
    downloads: contextDownloads,
    deleteDownloadById,
  } = useDatasetsAndNotebooks();
  const { sourceName: sourceNameParam } = useParams();
  const threePanelLayout = useThreePanelLayout({ storageKey: "datasets" });
  const tourContext = useTourContext();
  useTourStageSync(tourContext, sourceNameParam ? "grid" : "source");

  const [sources, setSources] = useState([]);
  const [sourcesLoading, setSourcesLoading] = useState(true);
  const [selectedDataset, setSelectedDataset] = useState(null);

  const [pendingSource, setPendingSource] = useState(null);

  const [downloadLoading, setDownloadLoading] = useState(false);

  const watchedJobsRef = useRef(new Set());

  // Derive selected source from URL param + loaded sources list
  const selectedSource =
    sources.find((s) => s.name === sourceNameParam) ?? null;
  const sourceDisplayName =
    selectedSource?.display_name || selectedSource?.name || sourceNameParam;

  useEffect(() => {
    getComponents({ selectTypes: "DatasetSource" })
      .then(setSources)
      .catch(() => setSources([]))
      .finally(() => setSourcesLoading(false));
  }, [t]);

  // Reset dataset selection when source changes
  useEffect(() => {
    setSelectedDataset(null);
  }, [sourceNameParam]);

  const downloads = useMemo(() => {
    const map = {};
    for (const r of contextDownloads) {
      map[`${r.source_name}::${r.dataset_id}`] = r;
    }
    return map;
  }, [contextDownloads]);

  useEffect(() => {
    const downloading = Object.values(downloads).filter(
      (d) => d.status === "downloading" && d.job_id,
    );

    for (const d of downloading) {
      if (watchedJobsRef.current.has(d.job_id)) continue;
      watchedJobsRef.current.add(d.job_id);

      const onDone = async (isError, job) => {
        try {
          const updated = await getDatafile(d.id);
          updateDownload(updated);
          if (job?.status === "cancelled") {
            enqueueSnackbar(t("common:jobQueue.jobCancelled"), {
              variant: "info",
            });
          } else if (isError) {
            enqueueSnackbar(
              `${t("hub:downloadFailed")}: ${d.name} - ${t("hub:checkQueue")}`,
              { variant: "error" },
            );
          } else {
            enqueueSnackbar(t("hub:downloaded") + `: ${d.name}`, {
              variant: "success",
            });
          }
        } catch {
          // ignore
        } finally {
          watchedJobsRef.current.delete(d.job_id);
        }
      };

      startJobPolling(
        d.job_id,
        () => onDone(false),
        (job) => onDone(true, job),
      );
    }
  }, [downloads]);

  const getDownloadForDataset = useCallback(
    (ds) => {
      if (!ds || !sourceNameParam) return null;
      return downloads[`${sourceNameParam}::${ds.id}`] ?? null;
    },
    [downloads, sourceNameParam],
  );

  const handleStartDownload = async () => {
    if (!selectedDataset || !sourceNameParam) return;
    setDownloadLoading(true);
    try {
      const row = await createDatafile(
        sourceNameParam,
        selectedDataset.id,
        selectedDataset.name,
        selectedDataset.description ?? "",
        selectedDataset.tags ?? [],
        selectedDataset.url ?? "",
      );
      const job = await enqueueDatafileJob(
        row.id,
        sourceNameParam,
        selectedDataset.id,
      );
      const entry = { ...row, job_id: job.id };
      addDownload(entry);
      if (isTourAtTarget(tourContext, "hub-dataset-action")) {
        tourContext.nextStep();
      }
    } catch {
      // error shown via download status
    } finally {
      setDownloadLoading(false);
    }
  };

  const handleDeleteDownload = async (downloadId) => {
    const name = contextDownloads.find((d) => d.id === downloadId)?.name ?? "";
    const success = await deleteDownloadById(downloadId);
    if (success) {
      enqueueSnackbar(t("hub:deleteSuccess", { name }), { variant: "success" });
    } else {
      enqueueSnackbar(t("hub:deleteError"), { variant: "error" });
    }
  };

  const handleImportDownload = (dl) => {
    navigate(`/app/data/hub/import/${dl.id}`);
  };

  const handleOpenSource = (source) => {
    navigate(`/app/data/hub/${source.name}`);
  };

  const handleStartImport = () => {
    const dl = getDownloadForDataset(selectedDataset);
    if (!dl) return;
    if (isTourAtTarget(tourContext, "hub-dataset-add")) {
      tourContext.markTourAsCompleted();
      tourContext.stopTour();
    }
    navigate(`/app/data/hub/import/${dl.id}`);
  };

  const handleSelectSource = (source) => {
    setPendingSource(source);
    if (
      source?.name === TOUR_SOURCE &&
      isTourAtTarget(tourContext, "hub-source-example")
    ) {
      goToTourTarget(tourContext, "hub-source-details");
    }
  };

  const handleSelectDataset = (ds) => {
    setSelectedDataset(ds);
    if (!isTourAtTarget(tourContext, "hub-iris-card")) return;
    // Skip what the dataset no longer needs: a finished download goes
    // straight to "Add to dashAI", one in progress to the datafiles list.
    const dl = getDownloadForDataset(ds);
    const target =
      !dl || dl.status === "error"
        ? "hub-dataset-action"
        : dl.status === "ready"
          ? "hub-dataset-add"
          : "hub-datafiles-list";
    goToTourTarget(tourContext, target);
  };

  return (
    <ThreePanelLayoutContext.Provider value={threePanelLayout}>
      <ModuleContainer>
        <LeftPanel>
          <DatasetsNotebooksLeftBar
            onToggle={threePanelLayout.handleToggleLeft}
          />
        </LeftPanel>

        <CenterPanel>
          {sourceNameParam ? (
            <DatasetGrid
              sourceName={sourceNameParam}
              sourceDisplayName={sourceDisplayName}
              selectedDataset={selectedDataset}
              onSelectDataset={handleSelectDataset}
            />
          ) : (
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                width: "100%",
                height: "100%",
                px: 4,
                pt: 4,
              }}
            >
              <HubBreadcrumbs />
              <Box sx={{ mb: 2 }}>
                <Typography variant="h5" component="h1">
                  {t("hub:selectSourceTitle")}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t("hub:selectSourceSubtitle")}
                </Typography>
              </Box>
              <Box sx={{ flex: 1, minHeight: 0, pb: 4 }}>
                <ComponentSelector
                  components={sources.map((s) => ({
                    ...s,
                    category: s.metadata?.category,
                  }))}
                  selected={pendingSource}
                  onSelect={handleSelectSource}
                  searchPlaceholder={t("hub:searchSources")}
                  tourDataFor={tourContext?.run ? "hub-source-example" : null}
                  tourDataMatchFn={(c) => c.name === TOUR_SOURCE}
                />
              </Box>
              <StepperNavigationFooter
                onBack={() => navigate("/app/data")}
                onNext={() => handleOpenSource(pendingSource)}
                nextDisabled={!pendingSource}
                nextDataTour="hub-source-next-button"
              />
            </Box>
          )}
        </CenterPanel>

        <RightPanel toggleButtonTop="50%">
          {!sourceNameParam ? (
            <ComponentDetailsPanel
              component={pendingSource}
              dataTour="hub-source-details"
            />
          ) : (
            <DatasetDetail
              dataset={selectedDataset}
              sourceName={sourceNameParam}
              download={getDownloadForDataset(selectedDataset)}
              downloadLoading={downloadLoading}
              onStartDownload={handleStartDownload}
              onStartImport={handleStartImport}
            />
          )}
        </RightPanel>
      </ModuleContainer>
    </ThreePanelLayoutContext.Provider>
  );
}
