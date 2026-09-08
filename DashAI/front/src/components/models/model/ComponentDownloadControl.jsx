import React, { useState, useEffect } from "react";
import {
  Box,
  Button,
  LinearProgress,
  Tooltip,
  Typography,
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import {
  downloadComponent,
  deleteComponentDownload,
  getComponentDownloadStatus,
} from "../../../api/component";
import { startJobPolling, stopJobPolling } from "../../../utils/jobPoller";
import DeleteConfirmationModal from "../../threeSectionLayout/DeleteConfirmationModal";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../../credentials/credentialStatus";

const formatSize = (bytes) => {
  if (bytes == null) return "";
  const mb = bytes / 1024 / 1024;
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${Math.round(mb)} MB`;
};

// Download state is a global, per-component fact (a component's artifacts are
// either on disk or not). The same component can be rendered by several
// controls at once (e.g. the same model selected at multiple nesting levels).
// This module-level pub/sub keeps every mounted control for a given component
// name in sync, and the cache lets a freshly mounted control pick up the
// latest known state instead of the (possibly stale) prop.
const downloadListeners = new Map(); // name -> Set<(state) => void>
const downloadStateCache = new Map(); // name -> { downloading, downloaded }
const anyChangeListeners = new Set(); // (name, state) => void
const activePollers = new Map(); // name -> poller id

const subscribeDownloadState = (name, listener) => {
  let listeners = downloadListeners.get(name);
  if (!listeners) {
    listeners = new Set();
    downloadListeners.set(name, listeners);
  }
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
};

// Read the last known download state for a component name, or undefined if it
// has not been tracked this session. Lets non-hook call sites (e.g. a bulk
// "run all" handler) consult the live state without subscribing.
export const getComponentDownloadState = (name) => downloadStateCache.get(name);

// Subscribe to every download/delete regardless of component name. Lets a
// container (e.g. a config dialog) re-check which nested components still need
// downloading after an inline control finishes.
export const subscribeAnyDownloadState = (listener) => {
  anyChangeListeners.add(listener);
  return () => {
    anyChangeListeners.delete(listener);
  };
};

const broadcastDownloadState = (name, state) => {
  downloadStateCache.set(name, { ...downloadStateCache.get(name), ...state });
  const listeners = downloadListeners.get(name);
  if (listeners) listeners.forEach((listener) => listener(state));
  anyChangeListeners.forEach((listener) => listener(name, state));
};

export const stopComponentDownloadPolling = (componentName) => {
  const pollerId = activePollers.get(componentName);
  if (pollerId != null) {
    stopJobPolling(pollerId);
    activePollers.delete(componentName);
  }
};

export const startComponentDownload = async ({
  component,
  enqueueSnackbar,
  t,
  onStatusChange,
}) => {
  broadcastDownloadState(component.name, { downloading: true });
  try {
    const { id } = await downloadComponent(component.name);
    activePollers.set(component.name, id);
    startJobPolling(
      id,
      async () => {
        activePollers.delete(component.name);
        const status = await getComponentDownloadStatus(component.name);
        broadcastDownloadState(component.name, {
          downloading: false,
          downloaded: status.downloaded,
        });
        if (onStatusChange) onStatusChange(status.downloaded);
        enqueueSnackbar(t("common:componentDownload.done"), {
          variant: "success",
        });
      },
      () => {
        activePollers.delete(component.name);
        broadcastDownloadState(component.name, {
          downloading: false,
          downloaded: false,
        });
        if (onStatusChange) onStatusChange(false);
        enqueueSnackbar(t("common:componentDownload.failed"), {
          variant: "error",
        });
      },
    );
  } catch (e) {
    broadcastDownloadState(component.name, {
      downloading: false,
      downloaded: false,
    });
    if (onStatusChange) onStatusChange(false);
    enqueueSnackbar(t("common:componentDownload.failed"), {
      variant: "error",
    });
  }
};

// Subscribe a component to the shared download state. Returns the live
// { downloaded, downloading } flags, kept in sync across every mounted control
// for the same component name.
export const useComponentDownloadState = (component) => {
  const cached = downloadStateCache.get(component.name);
  const [downloaded, setDownloaded] = useState(
    cached?.downloaded ?? Boolean(component.downloaded),
  );
  const [downloading, setDownloading] = useState(cached?.downloading ?? false);

  useEffect(() => {
    const known = downloadStateCache.get(component.name);
    setDownloaded(known?.downloaded ?? Boolean(component.downloaded));
    setDownloading(known?.downloading ?? false);
  }, [component.name, component.downloaded]);

  useEffect(() => {
    return subscribeDownloadState(component.name, (state) => {
      if (state.downloading !== undefined) setDownloading(state.downloading);
      if (state.downloaded !== undefined) setDownloaded(state.downloaded);
    });
  }, [component.name]);

  return { downloaded, downloading };
};

// A download-required model must be downloaded before it can be trained —
// otherwise clicking Train silently re-triggers a download for a model the
// user just deleted. Shared by every place a run's train/retrain action is
// gated on its model's download state (RunCard, ModelCardCompact,
// ModelDetailView).
export const useModelDownloadGate = (model, runModelName) => {
  const { downloaded, downloading } = useComponentDownloadState(
    model || { name: runModelName },
  );
  const modelNotDownloaded =
    Boolean(model?.metadata?.requires_download) &&
    !(downloaded && !downloading);

  return { modelNotDownloaded };
};

// Delete a component's download and broadcast the new state to every control.
export const deleteComponent = async ({
  component,
  enqueueSnackbar,
  t,
  onStatusChange,
}) => {
  try {
    await deleteComponentDownload(component.name);
    broadcastDownloadState(component.name, {
      downloading: false,
      downloaded: false,
    });
    if (onStatusChange) onStatusChange(false);
    enqueueSnackbar(t("common:componentDownload.deleted"), {
      variant: "success",
    });
  } catch {
    enqueueSnackbar(t("common:componentDownload.failed"), {
      variant: "error",
    });
  }
};

const ComponentDownloadControl = ({ component, onStatusChange }) => {
  const { t } = useTranslation(["common", "credentials"]);
  const { enqueueSnackbar } = useSnackbar();
  const meta = component.metadata || {};
  const { downloaded, downloading } = useComponentDownloadState(component);
  const { statuses, loaded } = useCredentialStatuses();
  const { locked, requiredPlatforms } = getComponentCredentialState(
    component,
    statuses,
    loaded,
  );
  const [confirmOpen, setConfirmOpen] = useState(false);

  if (!meta.requires_download) return null;

  const handleDownload = () =>
    startComponentDownload({ component, enqueueSnackbar, t, onStatusChange });

  const handleDelete = () =>
    deleteComponent({ component, enqueueSnackbar, t, onStatusChange });

  if (downloading) {
    return (
      <Box sx={{ my: 1 }}>
        <Typography variant="caption" color="text.secondary">
          {t("common:componentDownload.downloading")}
        </Typography>
        <LinearProgress sx={{ mt: 0.5 }} />
      </Box>
    );
  }

  if (downloaded) {
    return (
      <>
        <Button
          size="small"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={() => setConfirmOpen(true)}
        >
          {meta.download_size_bytes != null
            ? t("common:componentDownload.deleteWithSize", {
                size: formatSize(meta.download_size_bytes),
              })
            : t("common:componentDownload.delete")}
        </Button>
        <DeleteConfirmationModal
          open={confirmOpen}
          onClose={() => setConfirmOpen(false)}
          onConfirm={() => {
            setConfirmOpen(false);
            handleDelete();
          }}
          content={t("common:componentDownload.confirmDelete", {
            name: component.display_name || component.name,
          })}
        />
      </>
    );
  }

  // A component can only be downloaded once its required credentials are
  // authenticated, so block the download behind a disabled, explanatory button.
  if (locked) {
    return (
      <Tooltip
        title={t("credentials:requiredTooltip", {
          platform: requiredPlatforms,
        })}
      >
        <span>
          <Button
            size="small"
            variant="outlined"
            color="warning"
            startIcon={<DownloadIcon />}
            disabled
          >
            {t("credentials:authRequired", { platform: requiredPlatforms })}
          </Button>
        </span>
      </Tooltip>
    );
  }

  return (
    <Button
      size="small"
      variant="outlined"
      startIcon={<DownloadIcon />}
      onClick={handleDownload}
    >
      {t("common:componentDownload.download", {
        size: formatSize(meta.download_size_bytes),
      })}
    </Button>
  );
};

export default ComponentDownloadControl;
