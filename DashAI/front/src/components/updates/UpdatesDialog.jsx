import React from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ReactMarkdown from "react-markdown";
import { useTranslation } from "react-i18next";
import useUpdateInstall from "./useUpdateInstall";
import {
  UpdateInstallButton,
  UpdateInstallStatus,
} from "./UpdateInstallControls";

// Channels without an installer are updated from a terminal.
const UPDATE_COMMANDS = {
  pip: "pip install -U dashai",
  source: "git pull\nuv sync",
};

const INSTALLER_CHANNELS = ["windows", "macos", "appimage"];

function VersionRow({ label, value }) {
  return (
    <Stack direction="row" justifyContent="space-between" spacing={2}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 600 }}>
        {value}
      </Typography>
    </Stack>
  );
}

VersionRow.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
};

// Takes the namespace in each key: i18next-cli cannot tell which namespace a
// t function passed as an argument belongs to.
function statusMessage(info, t) {
  if (!info || info.check_failed) return t("updates:checkFailed");
  if (!info.enabled) return t("updates:disabled");
  if (info.update_available) {
    return t("updates:updateAvailable", { version: info.latest_version });
  }
  return t("updates:upToDate");
}

export default function UpdatesDialog({ open, onClose, info }) {
  const { t } = useTranslation("updates");
  const updateAvailable = Boolean(info?.update_available);
  const channel = info?.channel ?? "unknown";
  const command = UPDATE_COMMANDS[channel];
  const installerChannel = INSTALLER_CHANNELS.includes(channel);
  const downloadUrl =
    installerChannel && (info?.download_url || info?.release_url);
  const updater = useUpdateInstall(open && updateAvailable && installerChannel);
  // Installed from inside the app when the backend has a file for this
  // install; otherwise the user downloads it from the browser.
  const inAppUpdate = installerChannel && Boolean(updater.status?.available);

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle sx={{ pb: 1, bgcolor: "background.paper" }}>
        <Stack direction="row" alignItems="flex-start" spacing={1.5}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
              {t("title")}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t("subtitle")}
            </Typography>
          </Box>
          <IconButton
            onClick={onClose}
            aria-label="close"
            size="small"
            sx={{ mt: -0.5, mr: -0.5 }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
      </DialogTitle>
      <DialogContent
        dividers
        sx={{ pt: 3, pb: 3, bgcolor: "background.paper" }}
      >
        <Stack spacing={2}>
          <Stack spacing={0.75}>
            <VersionRow
              label={t("installedVersion")}
              value={info?.current_version ?? t("unknownVersion")}
            />
            {updateAvailable && (
              <VersionRow
                label={t("latestVersion")}
                value={info.latest_version}
              />
            )}
          </Stack>

          <Typography
            variant="body2"
            color={updateAvailable ? "primary" : "text.secondary"}
            sx={{ fontWeight: updateAvailable ? 600 : 400 }}
          >
            {statusMessage(info, t)}
          </Typography>

          {updateAvailable && info.release_notes && (
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                {t("releaseNotes")}
              </Typography>
              <Box
                sx={(theme) => ({
                  maxHeight: 240,
                  overflowY: "auto",
                  px: 2,
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 1,
                  typography: "body2",
                  "& a": { color: theme.palette.primary.main },
                  // GitHub release notes open with "## What's Changed"; keep
                  // headings at body size so they don't dominate the dialog.
                  "& h1, & h2, & h3, & h4": {
                    fontSize: theme.typography.body2.fontSize,
                    fontWeight: 600,
                    mt: 1.5,
                    mb: 0.5,
                  },
                })}
              >
                <ReactMarkdown
                  components={{
                    a: ({ href, children }) => (
                      <a href={href} target="_blank" rel="noopener noreferrer">
                        {children}
                      </a>
                    ),
                  }}
                >
                  {info.release_notes}
                </ReactMarkdown>
              </Box>
            </Box>
          )}

          {updateAvailable && (
            <Box>
              <Typography variant="body2" color="text.secondary">
                {t(`hint.${channel}`)}
              </Typography>
              {command && (
                <Box
                  component="pre"
                  sx={(theme) => ({
                    mt: 1,
                    mb: 0,
                    p: 1.5,
                    fontFamily: "monospace",
                    fontSize: 13,
                    whiteSpace: "pre-wrap",
                    background: theme.palette.action.hover,
                    borderRadius: 1,
                  })}
                >
                  {command}
                </Box>
              )}
            </Box>
          )}

          {updateAvailable && inAppUpdate && (
            <UpdateInstallStatus
              updater={updater}
              manualUrl={downloadUrl || undefined}
            />
          )}
        </Stack>
      </DialogContent>
      {updateAvailable && (
        <DialogActions sx={{ px: 3, py: 2, bgcolor: "background.paper" }}>
          {info.release_url && (
            <Button
              component="a"
              href={info.release_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {t("viewOnGitHub")}
            </Button>
          )}
          {inAppUpdate && (
            <UpdateInstallButton updater={updater} channel={channel} />
          )}
          {!inAppUpdate && downloadUrl && (
            <Button
              component="a"
              href={downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              variant="contained"
            >
              {t("download")}
            </Button>
          )}
        </DialogActions>
      )}
    </Dialog>
  );
}

UpdatesDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  info: PropTypes.shape({
    enabled: PropTypes.bool,
    channel: PropTypes.string,
    current_version: PropTypes.string,
    latest_version: PropTypes.string,
    update_available: PropTypes.bool,
    release_notes: PropTypes.string,
    release_url: PropTypes.string,
    download_url: PropTypes.string,
    check_failed: PropTypes.bool,
  }),
};
