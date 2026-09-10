import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box, Typography, Button, IconButton, Tooltip } from "@mui/material";
import { PlayArrow, Delete, Edit } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import ModelsBreadcrumbs from "./ModelsBreadcrumbs";
import RunCard from "./RunCard";
import RunEditDialog from "./RunEditDialog";
import RunStatusDot from "../shared/RunStatusDot";
import { useModelDownloadGate } from "./model/ComponentDownloadControl";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../credentials/credentialStatus";
import { canTrainRun, isRunActive } from "../../utils/runStatus";

/**
 * Full-screen detail view for a single model run: header with the run's
 * identity and actions, an edit dialog for its parameters, and RunCard's
 * tabs below. The column layout keeps the header fixed and lets RunCard (in
 * fillHeight mode) own the scroll.
 */
export default function ModelDetailView({
  run,
  models = [],
  session,
  onTrain,
  onDelete,
  explainerRefreshTrigger,
  onOperationsRefresh,
  existingRuns = [],
  onRefresh,
}) {
  const { t } = useTranslation(["models", "common", "credentials"]);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);

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

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
      }}
    >
      <Box sx={{ flexShrink: 0, px: 4, pt: 4 }}>
        <ModelsBreadcrumbs />

        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: 2,
            mb: 1,
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              flexWrap: "wrap",
            }}
          >
            <Typography variant="h5" sx={{ fontWeight: 700 }}>
              {run.name}
            </Typography>
            <Typography variant="body1" color="text.secondary">
              {modelDisplayName}
            </Typography>
            <RunStatusDot status={run.status} />
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            {canTrain && (
              <Tooltip
                title={
                  credentialsLocked
                    ? t("credentials:requiredTooltip", {
                        platform: requiredPlatforms,
                      })
                    : modelNotDownloaded
                      ? t("common:componentDownload.mustDownload")
                      : ""
                }
              >
                <span>
                  <Button
                    variant="contained"
                    size="small"
                    disabled={modelNotDownloaded || credentialsLocked}
                    startIcon={<PlayArrow />}
                    onClick={() => onTrain(run)}
                  >
                    {run.status === 3
                      ? t("common:retrain")
                      : t("common:trainVerb")}
                  </Button>
                </span>
              </Tooltip>
            )}
            <Tooltip title={t("common:edit")}>
              <IconButton size="small" onClick={() => setEditModalOpen(true)}>
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
        </Box>
      </Box>

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          px: 4,
          pb: 4,
        }}
      >
        <RunCard
          run={run}
          models={models}
          session={session}
          onTrain={onTrain}
          onDelete={onDelete}
          explainerRefreshTrigger={explainerRefreshTrigger}
          onOperationsRefresh={onOperationsRefresh}
          existingRuns={existingRuns}
          onRefresh={onRefresh}
          forceExpanded
          hideChrome
          deleteConfirmOpen={deleteConfirmOpen}
          setDeleteConfirmOpen={setDeleteConfirmOpen}
        />
      </Box>

      <RunEditDialog
        run={run}
        session={session}
        existingRuns={existingRuns}
        onRefresh={onRefresh}
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
      />
    </Box>
  );
}

ModelDetailView.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    model_name: PropTypes.string,
    status: PropTypes.number,
    created: PropTypes.string,
    start_time: PropTypes.string,
    end_time: PropTypes.string,
    parameters: PropTypes.object,
    optimizer_name: PropTypes.string,
    optimizer_parameters: PropTypes.object,
    goal_metric: PropTypes.string,
  }).isRequired,
  models: PropTypes.array,
  session: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    task_name: PropTypes.string,
  }),
  onTrain: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
  explainerRefreshTrigger: PropTypes.number,
  onOperationsRefresh: PropTypes.func,
  existingRuns: PropTypes.array,
  onRefresh: PropTypes.func,
};
