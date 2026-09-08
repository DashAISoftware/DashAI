import React, { useState, useEffect } from "react";
import { useStrategyKind } from "../../hooks/useStrategyKind";
import { STRATEGY_KINDS } from "../../utils/splitsPayload";
import PropTypes from "prop-types";
import {
  Box,
  Typography,
  TextField,
  CircularProgress,
  Tabs,
  Tab,
  Tooltip,
  Stack,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import {
  Search as SearchIcon,
  VpnKeyOutlined as KeyIcon,
} from "@mui/icons-material";
import { useSnackbar } from "notistack";
import { useParams } from "react-router-dom";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import ModelListItem from "./model/ModelListItem";
import {
  startComponentDownload,
  subscribeAnyDownloadState,
  useComponentDownloadState,
} from "./model/ComponentDownloadControl";
import ModelDownloadStatusIcon from "./model/ModelDownloadStatusIcon";
import CredentialsDialog from "../credentials/CredentialsDialog";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../credentials/credentialStatus";

/**
 * A single model row whose disabled state and download icon both derive from
 * the shared live download state, so they never disagree. While a download is
 * in progress the row stays disabled even if the backend already reports the
 * (partially written) files as present.
 */
function ModelRow({ model, onUse, onDownload, onNeedsCredentials, dataTour }) {
  const { t } = useTranslation(["credentials"]);
  const requiresDownload = Boolean(model.metadata?.requires_download);
  const { downloaded, downloading } = useComponentDownloadState(model);
  const { statuses, loaded } = useCredentialStatuses();
  const { locked, requiredPlatforms } = getComponentCredentialState(
    model,
    statuses,
    loaded,
  );
  // Usable only when credentials are satisfied AND (if needed) downloaded.
  const ready = !locked && (!requiresDownload || (downloaded && !downloading));

  const handleClick = () => {
    if (downloading) return;
    // Credentials gate first: block the download until they are authenticated.
    if (locked) {
      onNeedsCredentials(model);
      return;
    }
    if (ready) onUse(model);
    else onDownload(model);
  };

  // A locked row shows a key; when it also needs a download, the download
  // icon sits beside the key so both requirements are visible at a glance.
  const action =
    locked || requiresDownload ? (
      <Stack direction="row" spacing={0.5} alignItems="center">
        {locked && (
          <Tooltip
            title={t("credentials:requiredTooltip", {
              platform: requiredPlatforms,
            })}
          >
            <KeyIcon fontSize="small" color="warning" />
          </Tooltip>
        )}
        {requiresDownload && (
          <ModelDownloadStatusIcon model={model} disabled={locked} />
        )}
      </Stack>
    ) : null;

  return (
    <ModelListItem
      model={model}
      disabled={!ready}
      onClick={handleClick}
      onDisabledClick={handleClick}
      data-tour={dataTour}
      action={action}
    />
  );
}

ModelRow.propTypes = {
  model: PropTypes.object.isRequired,
  onUse: PropTypes.func.isRequired,
  onDownload: PropTypes.func.isRequired,
  onNeedsCredentials: PropTypes.func.isRequired,
  dataTour: PropTypes.string,
};
import { useTranslation } from "react-i18next";
import { useTourContext } from "../tour/TourProvider";
import { useModels } from "./ModelsContext";
import AddModelDialog from "./AddModelDialog";
import ColumnInsights from "../notebooks/dataset/ColumnInsights";
import RunInfoSidebar from "./RunInfoSidebar";
import ExplainersSidebar from "../explainers/ExplainersSidebar";
import StatisticalTestsList from "./StatisticalTestsList";
import StatisticalTestsModal from "./StatisticalTestsModal";

const EXPLAINERS_TAB = 1;

export default function ModelsRightBar({ onToggle }) {
  const theme = useTheme();
  const params = useParams();
  const isInModelDetail = Boolean(params.runId);
  const [models, setModels] = useState([]);
  const [filteredModels, setFilteredModels] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [credentialsDialogOpen, setCredentialsDialogOpen] = useState(false);
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["models", "common"]);
  const [activeTab, setActiveTab] = useState("models");

  const {
    selectedSession: session,
    onRunCreated,
    runs: existingRuns,
    selectModel,
    configOpen,
    selectedModel,
    closeConfig,
    datasetInfo,
    setDatasetTab,
    sessionRightContent,
    runDetailTab,
    triggerExplainerRefresh,
    datasets,
    tasks,
    openStatisticalTest,
    closeStatisticalTest,
    selectedStatisticalTest,
    statisticalTestsModalOpen,
    getModelsForTask,
  } = useModels();

  const fetchModels = React.useCallback(async () => {
    try {
      setLoading(true);
      const response = await getModelsForTask(session.task_name);
      setModels(response);
      setFilteredModels(response);
    } catch (error) {
      console.error("Error fetching models:", error);
      enqueueSnackbar(t("models:error.fetchingModels"), {
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [session?.task_name, getModelsForTask, enqueueSnackbar, t]);

  useEffect(() => {
    if (session) {
      fetchModels();
    } else {
      setModels([]);
      setFilteredModels([]);
      setSearchQuery("");
    }
  }, [session, fetchModels]);

  // When any download finishes (or is deleted) update just that model's flag in
  // place. A full refetch would flip `loading`, swap the list for a spinner and
  // reset the scroll position; an in-place update keeps the list mounted and
  // keeps `downloaded` accurate for the model passed on to the config dialog.
  useEffect(() => {
    if (!session) return undefined;
    return subscribeAnyDownloadState((name, state) => {
      if (state.downloaded === undefined) return;
      setModels((prev) =>
        prev.map((model) =>
          model.name === name
            ? { ...model, downloaded: state.downloaded }
            : model,
        ),
      );
    });
  }, [session]);

  // Filter models based on search
  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredModels(models);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredModels(
        models.filter(
          (model) =>
            (model.display_name || model.name).toLowerCase().includes(query) ||
            (model.metadata?.description || "").toLowerCase().includes(query),
        ),
      );
    }
  }, [searchQuery, models]);

  const tourContext = useTourContext();

  // Determine if statistical tests should be shown (only for nested CV sessions)
  const isCv =
    useStrategyKind(session?.evaluation_strategy) === STRATEGY_KINDS.CV;

  useEffect(() => {
    if (!isCv) {
      setActiveTab("models");
      closeStatisticalTest();
    }
  }, [isCv, closeStatisticalTest]);

  const handleUseModel = (model) => {
    if (!session) {
      enqueueSnackbar(t("models:error.selectSessionFirst"), {
        variant: "warning",
      });
      return;
    }
    selectModel(model);
    if (tourContext?.run && tourContext?.stepIndex === 2) {
      const waitForElement = () => {
        const element = document.querySelector('[data-tour="model-config"]');
        if (element) {
          tourContext.nextStep();
        } else {
          setTimeout(waitForElement, 100);
        }
      };
      setTimeout(waitForElement, 300);
    }
  };

  const handleDownloadModel = (model) => {
    if (!session) {
      enqueueSnackbar(t("models:error.selectSessionFirst"), {
        variant: "warning",
      });
      return;
    }
    // Completion is reflected by the shared download-state subscription above,
    // which updates the model's flag in place without a scroll-resetting
    // refetch.
    startComponentDownload({ component: model, enqueueSnackbar, t });
  };

  const activeRun = isInModelDetail
    ? existingRuns.find((r) => String(r.id) === params.runId)
    : null;

  if (isInModelDetail && activeRun) {
    // On the explainers tab of a finished run, offer the compatible
    // explainers to add, mirroring how the session view offers models.
    if (runDetailTab === EXPLAINERS_TAB && activeRun.status === 3) {
      return (
        <ExplainersSidebar
          run={activeRun}
          session={session}
          onCreated={triggerExplainerRefresh}
        />
      );
    }
    const activeModel = models.find((m) => m.name === activeRun.model_name);
    const datasetName = datasets.find(
      (d) => d.id === session?.dataset_id,
    )?.name;
    return (
      <RunInfoSidebar
        run={activeRun}
        model={activeModel}
        datasetName={datasetName}
        session={session}
        datasets={datasets}
        tasks={tasks}
      />
    );
  }

  if (sessionRightContent) {
    return (
      <SideBar>
        <Box
          sx={{
            p: 2,
            borderBottom: `1px solid ${theme.palette.ui.border}`,
            flexShrink: 0,
            height: 64,
            display: "flex",
            alignItems: "center",
          }}
        >
          <Typography variant="h6" color="text.primary">
            {t("models:label.configureSession")}
          </Typography>
        </Box>
        <Box sx={{ flex: 1, overflowY: "auto", p: 2 }}>
          {sessionRightContent}
        </Box>
      </SideBar>
    );
  }

  return (
    <SideBar>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          height: "100%",
          width: "100%",
        }}
      >
        {/* Header with tabs */}
        <Box
          sx={{
            borderBottom: `1px solid ${theme.palette.ui.border}`,
            flexShrink: 0,
          }}
        >
          <Box
            sx={{
              p: 2,
              height: 64,
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-start",
            }}
          >
            <Typography variant="h6" color="text.primary">
              {activeTab === "models"
                ? t("models:label.availableModels")
                : t("models:label.statisticalTests")}
            </Typography>
          </Box>
          {isCv && (
            <Tabs
              value={activeTab}
              onChange={(e, newValue) => setActiveTab(newValue)}
              sx={{
                px: 2,
                borderTop: `1px solid ${theme.palette.ui.border}`,
              }}
              variant="fullWidth"
            >
              <Tab
                label={t("models:label.availableModels")}
                value="models"
                sx={{ textTransform: "none", fontSize: "0.9rem" }}
              />
              <Tab
                label={t("models:label.statisticalTests")}
                value="tests"
                sx={{ textTransform: "none", fontSize: "0.9rem" }}
              />
            </Tabs>
          )}
        </Box>

        {/* Content */}
        {!session ? (
          datasetInfo ? (
            <Box sx={{ flex: 1, overflowY: "auto" }}>
              <ColumnInsights
                numericStats={datasetInfo?.numeric_stats}
                textStats={datasetInfo?.text_stats}
                onNavigateTab={setDatasetTab}
              />
            </Box>
          ) : (
            <Box
              sx={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                p: 2,
              }}
            >
              <Typography
                variant="body2"
                sx={{ color: "text.secondary", textAlign: "center" }}
              >
                {t("models:label.selectSessionToViewModels")}
              </Typography>
            </Box>
          )
        ) : isInModelDetail ? (
          <Box
            sx={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              p: 2,
            }}
          >
            <Typography
              variant="body2"
              sx={{ color: "text.secondary", textAlign: "center" }}
            >
              {t("models:label.exitModelDetailToAddModels")}
            </Typography>
          </Box>
        ) : activeTab === "models" ? (
          <>
            {/* Search Box */}
            <Box sx={{ p: 4, flexShrink: 0 }}>
              <TextField
                fullWidth
                size="small"
                placeholder={t("models:label.searchModels")}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                slotProps={{
                  input: {
                    startAdornment: (
                      <SearchIcon sx={{ mr: 2, color: "text.secondary" }} />
                    ),
                  },
                }}
              />
            </Box>

            {/* Models List */}
            <Box sx={{ flex: 1, overflow: "auto", p: 4 }}>
              {loading ? (
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    height: "100%",
                  }}
                >
                  <CircularProgress size={32} />
                </Box>
              ) : filteredModels.length === 0 ? (
                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "center",
                    alignItems: "center",
                    height: "100%",
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{ color: "text.secondary", textAlign: "center" }}
                  >
                    {searchQuery
                      ? t("models:label.noModelsMatchSearch")
                      : t("models:label.noCompatibleModelsFound")}
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                  {filteredModels.map((model, index) => (
                    <ModelRow
                      key={model.name}
                      model={model}
                      onUse={handleUseModel}
                      onDownload={handleDownloadModel}
                      onNeedsCredentials={() => setCredentialsDialogOpen(true)}
                      dataTour={index === 0 ? "first-model" : undefined}
                    />
                  ))}
                </Box>
              )}
            </Box>
          </>
        ) : (
          /* Statistical Tests Tab */
          <StatisticalTestsList onTestSelect={openStatisticalTest} />
        )}
      </Box>

      {/* Modals */}
      <AddModelDialog
        open={configOpen}
        onClose={closeConfig}
        preselectedModel={selectedModel?.name}
        preselectedModelObject={selectedModel}
        session={session}
        existingRuns={existingRuns}
        onRunCreated={onRunCreated}
      />
      <StatisticalTestsModal
        test={selectedStatisticalTest}
        runs={existingRuns}
        session={session}
        open={statisticalTestsModalOpen && isCv}
        onClose={closeStatisticalTest}
      />
      <CredentialsDialog
        open={credentialsDialogOpen}
        onClose={() => setCredentialsDialogOpen(false)}
      />
    </SideBar>
  );
}

ModelsRightBar.propTypes = {
  onToggle: PropTypes.func.isRequired,
};
