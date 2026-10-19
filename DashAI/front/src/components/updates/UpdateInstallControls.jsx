import React from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  LinearProgress,
  Stack,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";

const formatSize = (bytes) => {
  if (bytes == null) return "";
  const mb = bytes / 1024 / 1024;
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${Math.round(mb)} MB`;
};

const updaterShape = PropTypes.shape({
  status: PropTypes.shape({
    available: PropTypes.bool,
    size: PropTypes.number,
    downloaded: PropTypes.bool,
  }),
  phase: PropTypes.string.isRequired,
  progress: PropTypes.number,
  error: PropTypes.shape({
    kind: PropTypes.string,
    detail: PropTypes.string,
  }),
  installedChannel: PropTypes.string,
  startDownload: PropTypes.func.isRequired,
  install: PropTypes.func.isRequired,
  cancelConfirm: PropTypes.func.isRequired,
});

/** Progress, confirmation and result messages of an in-app update. */
export function UpdateInstallStatus({ updater, manualUrl }) {
  const { t } = useTranslation("updates");
  const { phase, progress, error, installedChannel } = updater;

  if (phase === "downloading") {
    return (
      <Box>
        <LinearProgress
          variant={progress == null ? "indeterminate" : "determinate"}
          value={progress ?? 0}
        />
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: "block", mt: 0.75 }}
        >
          {progress == null
            ? t("downloadingShort")
            : t("downloading", { percent: Math.round(progress) })}
        </Typography>
      </Box>
    );
  }

  if (phase === "confirm") {
    return (
      <Alert severity="warning">
        {t("jobsRunningWarning")}
        <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
          <Button
            color="inherit"
            size="small"
            variant="outlined"
            onClick={() => updater.install(true)}
          >
            {t("installAnyway")}
          </Button>
          <Button color="inherit" size="small" onClick={updater.cancelConfirm}>
            {t("cancel")}
          </Button>
        </Stack>
      </Alert>
    );
  }

  if (phase === "installed") {
    return (
      <Alert severity="success">{t(`installed.${installedChannel}`)}</Alert>
    );
  }

  if (phase === "error") {
    return (
      <Alert severity="error">
        {error?.kind === "install"
          ? t("installFailed", { error: error.detail ?? "" })
          : t("downloadFailed")}
        {manualUrl && (
          <Box sx={{ mt: 1 }}>
            <Button
              color="inherit"
              size="small"
              variant="outlined"
              component="a"
              href={manualUrl}
              target="_blank"
              rel="noopener noreferrer"
            >
              {t("manualDownload")}
            </Button>
          </Box>
        )}
      </Alert>
    );
  }

  return null;
}

UpdateInstallStatus.propTypes = {
  updater: updaterShape.isRequired,
  manualUrl: PropTypes.string,
};

/** The main dialog action: download the update, then install it. */
export function UpdateInstallButton({ updater, channel }) {
  const { t } = useTranslation("updates");
  const { status, phase } = updater;

  if (phase === "confirm" || phase === "installed") return null;

  if (phase === "downloading" || phase === "installing") {
    return (
      <Button variant="contained" disabled>
        {phase === "downloading" ? t("downloadingShort") : t("installing")}
      </Button>
    );
  }

  if (status?.downloaded) {
    return (
      <Button variant="contained" onClick={() => updater.install(false)}>
        {channel === "macos" ? t("openInstaller") : t("installRestart")}
      </Button>
    );
  }

  return (
    <Button variant="contained" onClick={updater.startDownload}>
      {t("downloadUpdate", { size: formatSize(status?.size) })}
    </Button>
  );
}

UpdateInstallButton.propTypes = {
  updater: updaterShape.isRequired,
  channel: PropTypes.string.isRequired,
};
