import React, { useState, useEffect, useCallback } from "react";
import PropTypes from "prop-types";
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  IconButton,
  Button,
  Collapse,
  Tooltip,
} from "@mui/material";
import { useTheme, alpha } from "@mui/material/styles";
import {
  PlayArrow,
  Stop,
  Edit,
  Delete,
  ExpandMore,
  ExpandLess,
} from "@mui/icons-material";
import {
  getRunStatus,
  getRunStatusColor,
  canTrainRun,
  isRunActive,
} from "../../utils/runStatus";
import RunResults from "./RunResults";
import RunEditDialog from "./RunEditDialog";
import { getRunOperationsCount } from "../../api/run";
import { useModelDownloadGate } from "./model/ComponentDownloadControl";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../credentials/credentialStatus";
import { useTranslation } from "react-i18next";
import DeleteConfirmationModal from "../threeSectionLayout/DeleteConfirmationModal";

/**
 * Card component displaying a model run with actions and details
 */
function RunCard({
  run,
  models = [],
  session,
  onTrain,
  onDelete,
  onOperationsRefresh,
  explainerRefreshTrigger,
  isLastRun = false,
  existingRuns = [],
  onRefresh,
  isHighlighted = false,
  forceExpanded = false,
  hideChrome = false,
  isEditing: controlledIsEditing = undefined,
  setIsEditing: setControlledIsEditing = undefined,
  deleteConfirmOpen: controlledDeleteConfirmOpen = undefined,
  setDeleteConfirmOpen: setControlledDeleteConfirmOpen = undefined,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["models", "common", "credentials"]);
  const [resultsVisible, setResultsVisible] = useState(() => {
    if (run.status === 0) return false;
    const saved = localStorage.getItem(`run-${run.id}-results-visible`);
    return saved ? JSON.parse(saved) : false;
  });
  const isResultsVisible = forceExpanded || resultsVisible;

  useEffect(() => {
    if (forceExpanded) return;
    localStorage.setItem(
      `run-${run.id}-results-visible`,
      JSON.stringify(resultsVisible),
    );
  }, [resultsVisible, run.id, forceExpanded]);

  const isEditingControlled = controlledIsEditing !== undefined;
  const [internalIsEditing, setInternalIsEditing] = useState(false);
  const isEditing = isEditingControlled
    ? controlledIsEditing
    : internalIsEditing;
  const setIsEditing = isEditingControlled
    ? setControlledIsEditing
    : setInternalIsEditing;

  const isDeleteConfirmControlled = controlledDeleteConfirmOpen !== undefined;
  const [internalDeleteConfirmOpen, setInternalDeleteConfirmOpen] =
    useState(false);
  const deleteConfirmOpen = isDeleteConfirmControlled
    ? controlledDeleteConfirmOpen
    : internalDeleteConfirmOpen;
  const setDeleteConfirmOpen = isDeleteConfirmControlled
    ? setControlledDeleteConfirmOpen
    : setInternalDeleteConfirmOpen;
  const [operationsCount, setOperationsCount] = useState(null);
  const [autoExpand, setAutoExpand] = useState(false);

  const fetchOperationsCount = useCallback(async () => {
    if (!run?.id) return;
    try {
      const count = await getRunOperationsCount(run.id.toString());
      setOperationsCount(count);
    } catch (error) {
      console.error("Error fetching operations count:", error);
    }
  }, [run?.id]);

  useEffect(() => {
    fetchOperationsCount();
  }, [fetchOperationsCount, explainerRefreshTrigger]);

  const statusText = getRunStatus(run.status, t);
  const model = models.find((m) => m.name === run.model_name);
  const modelDisplayName = model?.display_name || run.model_name;

  // A download-required model must be downloaded before it can be trained.
  // Track the live download state so the button reflects an inline download.
  const { modelNotDownloaded } = useModelDownloadGate(model, run.model_name);

  // A model whose required credentials are unmet cannot be trained. Derived
  // from the live credential store so the button reacts to verification.
  const { statuses, loaded } = useCredentialStatuses();
  const { locked: credentialsLocked, requiredPlatforms } =
    getComponentCredentialState(model || {}, statuses, loaded);

  useEffect(() => {
    if (run.status !== 1 && run.status !== 2) {
      setAutoExpand(false);
    }
  }, [run.status]);

  const canTrain = canTrainRun(run.status);
  const isRunning = isRunActive(run.status);

  const getMetrics = () => {
    if (!run.trained_models || run.trained_models.length === 0) {
      return null;
    }

    const metrics = {};
    run.trained_models.forEach((model) => {
      if (model.metrics) {
        Object.entries(model.metrics).forEach(([key, value]) => {
          if (!metrics[key]) metrics[key] = [];
          metrics[key].push(value);
        });
      }
    });

    return metrics;
  };

  const metrics = getMetrics();

  return (
    <Card
      elevation={hideChrome ? 0 : 2}
      sx={
        hideChrome
          ? {
              bgcolor: "transparent",
              boxShadow: "none",
              display: "flex",
              flexDirection: "column",
              flex: 1,
              minHeight: 0,
            }
          : {
              mb: 4,
              bgcolor: "background.box",
              borderLeft: "4px solid",
              borderLeftColor:
                run.status === 3 // Finished
                  ? "success.main"
                  : run.status === 4 // Error
                    ? "error.main"
                    : isRunning
                      ? "info.main"
                      : "divider",
              position: "relative",
              zIndex: isHighlighted ? 1 : 0,
              "@keyframes newRunHighlight": {
                "0%": { boxShadow: "none" },
                "20%": {
                  boxShadow: `0 0 0 3px ${alpha(
                    theme.palette.primary.main,
                    0.65,
                  )}, 0 0 24px 8px ${alpha(theme.palette.primary.main, 0.2)}`,
                },
                "100%": { boxShadow: "none" },
              },
              animation: isHighlighted
                ? "newRunHighlight 4s ease-in-out forwards"
                : "none",
            }
      }
    >
      <CardContent
        sx={
          hideChrome
            ? {
                p: 0,
                "&:last-child": { pb: 0 },
                display: "flex",
                flexDirection: "column",
                flex: 1,
                minHeight: 0,
              }
            : undefined
        }
      >
        {!hideChrome && (
          <>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                mb: 4,
                gap: 2,
              }}
            >
              <Box
                sx={{ display: "flex", alignItems: "center", gap: 2, flex: 1 }}
              >
                <Typography
                  variant="h6"
                  component="div"
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    flexWrap: "wrap",
                  }}
                >
                  {run.name}
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    component="span"
                  >
                    ({modelDisplayName})
                  </Typography>
                </Typography>
              </Box>

              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                {!isRunning && (
                  <Button
                    variant="outlined"
                    size="small"
                    color="primary"
                    startIcon={<Edit />}
                    onClick={() => setIsEditing(true)}
                  >
                    {t("common:edit")}
                  </Button>
                )}
                {canTrain && (
                  <Tooltip
                    title={
                      credentialsLocked
                        ? t("credentials:requiredTooltip", {
                            platform: requiredPlatforms,
                          })
                        : modelNotDownloaded
                          ? t("common:componentDownload.mustDownload")
                          : run.status === 3 &&
                              operationsCount &&
                              (operationsCount.explainers > 0 ||
                                operationsCount.predictions > 0)
                            ? t("models:message.retrainWillResetOperations", {
                                explainersCount: operationsCount.explainers,
                                predictionsCount: operationsCount.predictions,
                              })
                            : ""
                    }
                  >
                    <span>
                      <Button
                        variant="contained"
                        color="primary"
                        size="small"
                        disabled={modelNotDownloaded || credentialsLocked}
                        startIcon={<PlayArrow />}
                        onClick={() => {
                          setAutoExpand(true);
                          onTrain(run, operationsCount);
                        }}
                        data-tour={isLastRun ? "train-button" : undefined}
                      >
                        {run.status === 3
                          ? t("common:retrain")
                          : t("common:trainVerb")}
                      </Button>
                    </span>
                  </Tooltip>
                )}
                {isRunning && (
                  <Button
                    variant="contained"
                    color="warning"
                    size="small"
                    disabled
                    startIcon={<Stop />}
                  >
                    {t("common:running")}
                  </Button>
                )}

                <Chip
                  label={statusText}
                  color={getRunStatusColor(run.status)}
                  size="small"
                />

                <Tooltip title={t("models:button.deleteRun")}>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => setDeleteConfirmOpen(true)}
                    disabled={isRunning}
                  >
                    <Delete fontSize="small" />
                  </IconButton>
                </Tooltip>
                {!forceExpanded && (
                  <Tooltip
                    title={
                      resultsVisible
                        ? t("models:label.hideResults")
                        : t("models:label.showResults")
                    }
                  >
                    <IconButton
                      size="small"
                      onClick={() => setResultsVisible(!resultsVisible)}
                      color="default"
                    >
                      {resultsVisible ? (
                        <ExpandLess fontSize="small" />
                      ) : (
                        <ExpandMore fontSize="small" />
                      )}
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            </Box>

            {metrics && Object.keys(metrics).length > 0 && (
              <Box sx={{ mb: 4 }}>
                <Typography variant="subtitle2" gutterBottom>
                  {t("common:metrics")}
                </Typography>
                <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                  {Object.entries(metrics).map(([metric, values]) => {
                    const avgValue =
                      values.reduce((sum, val) => sum + val, 0) / values.length;
                    return (
                      <Box key={metric}>
                        <Typography
                          variant="caption"
                          sx={{ color: theme.palette.text.secondary }}
                        >
                          {metric.toUpperCase()}
                        </Typography>
                        <Typography variant="body2" fontWeight="medium">
                          {avgValue.toFixed(4)}
                        </Typography>
                      </Box>
                    );
                  })}
                </Box>
              </Box>
            )}

            {run.description && (
              <Typography
                variant="body2"
                sx={{ color: theme.palette.text.secondary, mb: 4 }}
              >
                {run.description}
              </Typography>
            )}
          </>
        )}

        <Box
          sx={
            hideChrome
              ? {
                  display: "flex",
                  flexDirection: "column",
                  flex: 1,
                  minHeight: 0,
                }
              : { mt: 4 }
          }
        >
          <RunResults
            run={run}
            session={session}
            onRefresh={onOperationsRefresh}
            explainerRefreshTrigger={explainerRefreshTrigger}
            resultsVisible={isResultsVisible}
            setResultsVisible={setResultsVisible}
            autoExpand={autoExpand}
            fillHeight={hideChrome}
          />
        </Box>
        <DeleteConfirmationModal
          open={deleteConfirmOpen}
          onClose={() => setDeleteConfirmOpen(false)}
          onConfirm={() => {
            setDeleteConfirmOpen(false);
            localStorage.removeItem(`run-${run.id}-results-visible`);
            localStorage.removeItem(`run-${run.id}-active-tab`);
            onDelete(run);
          }}
          content={t("models:message.confirmDeleteRun")}
        />
      </CardContent>

      <RunEditDialog
        run={run}
        session={session}
        existingRuns={existingRuns}
        onRefresh={onRefresh}
        open={isEditing}
        onClose={() => setIsEditing(false)}
      />
    </Card>
  );
}

RunCard.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    model_name: PropTypes.string,
    status: PropTypes.number,
    parameters: PropTypes.object,
    optimizer_name: PropTypes.string,
    optimizer_parameters: PropTypes.object,
    goal_metric: PropTypes.string,
    description: PropTypes.string,
    created: PropTypes.string,
    trained_models: PropTypes.array,
    model_session_id: PropTypes.number,
  }).isRequired,
  models: PropTypes.array,
  session: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    task_name: PropTypes.string,
  }),
  onTrain: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onOperationsRefresh: PropTypes.func,
  explainerRefreshTrigger: PropTypes.number,
  isLastRun: PropTypes.bool,
  existingRuns: PropTypes.array,
  onRefresh: PropTypes.func,
  forceExpanded: PropTypes.bool,
  hideChrome: PropTypes.bool,
  isEditing: PropTypes.bool,
  setIsEditing: PropTypes.func,
  deleteConfirmOpen: PropTypes.bool,
  setDeleteConfirmOpen: PropTypes.func,
};

export default RunCard;
