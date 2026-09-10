import React, { useState } from "react";
import PropTypes from "prop-types";
import { Paper, Box, Typography, IconButton, Tooltip } from "@mui/material";
import { useTheme, alpha } from "@mui/material/styles";
import { PlayArrow, Delete, ChevronRight, Edit } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import {
  canTrainRun,
  isRunActive,
  getRunStatusColor,
} from "../../utils/runStatus";
import { ModelIcon } from "./model/ModelIcon";
import DeleteConfirmationModal from "../threeSectionLayout/DeleteConfirmationModal";
import RunEditDialog from "./RunEditDialog";
import RunStatusDot from "../shared/RunStatusDot";
import { useModelDownloadGate } from "./model/ComponentDownloadControl";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../credentials/credentialStatus";

/**
 * Compact launcher card for a single run — shows just enough to identify
 * the model and its state, and opens the full-screen model detail view.
 */
function ModelCardCompact({
  run,
  models = [],
  session,
  existingRuns = [],
  onTrain,
  onDelete,
  onRefresh,
  onOpen,
  isHighlighted = false,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["models", "common", "credentials"]);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [configOpen, setConfigOpen] = useState(false);

  const model = models.find((m) => m.name === run.model_name);
  const modelDisplayName = model?.display_name || run.model_name;
  const canTrain = canTrainRun(run.status);
  const isRunning = isRunActive(run.status);

  // A download-required model must be downloaded before it can be trained —
  // otherwise clicking Train silently re-triggers a download for a model the
  // user just deleted. Mirrors the same gate in RunCard.
  const { modelNotDownloaded } = useModelDownloadGate(model, run.model_name);

  // A model whose required credentials are unmet cannot be trained. Derived
  // from the live credential store so the button reacts to verification.
  const { statuses, loaded } = useCredentialStatuses();
  const { locked: credentialsLocked, requiredPlatforms } =
    getComponentCredentialState(model || {}, statuses, loaded);

  const statusColorKey = getRunStatusColor(run.status);
  const statusMain =
    statusColorKey === "default"
      ? theme.palette.text.disabled
      : theme.palette[statusColorKey].main;

  return (
    <Paper
      elevation={0}
      onClick={onOpen}
      sx={{
        display: "flex",
        flexDirection: "column",
        cursor: "pointer",
        border: 1,
        borderColor: alpha(statusMain, 0.35),
        transition:
          "border-color 0.15s, box-shadow 0.2s ease-out, transform 0.15s ease-out",
        "&:hover": {
          borderColor: theme.palette.primary.main,
          transform: "translateY(-3px)",
          boxShadow: `0 6px 16px ${alpha(theme.palette.common.black, 0.35)}`,
          "& .card-chevron-icon": { color: theme.palette.primary.main },
        },
        ...(isHighlighted && {
          transition:
            "border-color 0.15s, box-shadow 1.2s ease-out, transform 0.15s ease-out",
          boxShadow: `0 0 0 3px ${alpha(
            theme.palette.primary.main,
            0.4,
          )}, 0 0 20px 6px ${alpha(theme.palette.primary.main, 0.18)}`,
        }),
      }}
    >
      <Box
        sx={{
          pt: 1.5,
          pb: 2.5,
          px: 2.5,
          display: "flex",
          alignItems: "center",
          gap: 2,
        }}
      >
        <Box
          sx={{
            p: 1.5,
            borderRadius: 1,
            bgcolor: "action.hover",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <ModelIcon
            iconName={model?.metadata?.icon}
            color={model?.color || model?.metadata?.color}
          />
        </Box>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="subtitle2" noWrap sx={{ fontWeight: 600 }}>
            {run.name}
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <RunStatusDot status={run.status} size={6} />
            <Typography
              variant="caption"
              color="text.secondary"
              noWrap
              sx={{ lineHeight: 1 }}
            >
              {modelDisplayName}
            </Typography>
          </Box>
        </Box>

        <Box
          sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
          onClick={(e) => e.stopPropagation()}
        >
          {canTrain && (
            <Tooltip
              title={
                credentialsLocked
                  ? t("credentials:requiredTooltip", {
                      platform: requiredPlatforms,
                    })
                  : modelNotDownloaded
                    ? t("common:componentDownload.mustDownload")
                    : run.status === 3
                      ? t("common:retrain")
                      : t("common:trainVerb")
              }
            >
              <span>
                <IconButton
                  size="small"
                  disabled={modelNotDownloaded || credentialsLocked}
                  onClick={() => onTrain(run)}
                >
                  <PlayArrow fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          )}
          <Tooltip title={t("common:edit")}>
            <IconButton size="small" onClick={() => setConfigOpen(true)}>
              <Edit fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={t("models:button.deleteRun")}>
            <IconButton
              size="small"
              color="error"
              disabled={isRunning}
              onClick={() => setDeleteConfirmOpen(true)}
            >
              <Delete fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        {/* Wrapped so clicks inside the modal (a portal) don't bubble through
            the React tree into the card's onClick={onOpen} above */}
        <Box onClick={(e) => e.stopPropagation()}>
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

          <RunEditDialog
            run={run}
            session={session}
            existingRuns={existingRuns}
            onRefresh={onRefresh}
            open={configOpen}
            onClose={() => setConfigOpen(false)}
          />
        </Box>
      </Box>

      {/* Footer hint — signals the whole card is clickable to open the
          full model detail view (configuration, metrics, predictions, etc.) */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          px: 2.5,
          pt: 0.75,
          pb: 1.5,
        }}
      >
        <Typography
          variant="caption"
          color="text.disabled"
          sx={{
            fontSize: "0.6rem",
            fontWeight: 500,
            letterSpacing: 0.4,
            textTransform: "uppercase",
          }}
        >
          {t("models:label.metrics")} | {t("models:label.operations")}
        </Typography>
        <ChevronRight
          className="card-chevron-icon"
          sx={{
            fontSize: 16,
            color: "text.disabled",
            transition: "color 0.15s",
          }}
        />
      </Box>
    </Paper>
  );
}

ModelCardCompact.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    model_name: PropTypes.string,
    status: PropTypes.number,
    goal_metric: PropTypes.string,
    trained_models: PropTypes.array,
  }).isRequired,
  models: PropTypes.array,
  session: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    task_name: PropTypes.string,
  }),
  existingRuns: PropTypes.array,
  onTrain: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  onRefresh: PropTypes.func,
  onOpen: PropTypes.func.isRequired,
  isHighlighted: PropTypes.bool,
};

export default ModelCardCompact;
