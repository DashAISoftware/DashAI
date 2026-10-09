import { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Box, MenuItem, Select, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { getRelatedComponents } from "../../api/generativeTask";
import { updateGenerativeSession } from "../../api/session";
import {
  getComponentDownloadState,
  subscribeAnyDownloadState,
} from "../models/model/ComponentDownloadControl";

/**
 * Session-level model switcher: lets the user change the model used by a
 * generative session, restricted to models of the same task. Models that are
 * download-required but not yet downloaded are shown disabled.
 */
export default function ModelSwitcher({
  sessionId,
  taskName,
  currentModelName,
  onChanged,
}) {
  const { t } = useTranslation(["generative", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const [models, setModels] = useState([]);
  const [saving, setSaving] = useState(false);
  // Bump to re-render when any download state changes so the labels reflect
  // downloads that finished after the model list was fetched.
  const [, setDownloadVersion] = useState(0);

  useEffect(() => {
    if (!taskName) return;
    getRelatedComponents(taskName)
      .then((components) => setModels(components || []))
      .catch(() => setModels([]));
  }, [taskName]);

  useEffect(
    () => subscribeAnyDownloadState(() => setDownloadVersion((v) => v + 1)),
    [],
  );

  const handleChange = async (event) => {
    const newModel = event.target.value;
    if (!newModel || newModel === currentModelName) return;
    setSaving(true);
    try {
      await updateGenerativeSession({
        id: sessionId,
        formData: { model_name: newModel },
      });
      if (onChanged) onChanged(newModel);
    } catch (error) {
      const status = error?.response?.status;
      enqueueSnackbar(
        status === 409
          ? t("common:componentDownload.mustDownload")
          : t("generative:error.modelSwitchFailed"),
        { variant: "error" },
      );
    } finally {
      setSaving(false);
    }
  };

  // Ensure the current model is always a selectable value even if the list
  // has not loaded yet (avoids an out-of-range MUI Select warning).
  const hasCurrent = models.some((m) => m.name === currentModelName);
  const options = hasCurrent
    ? models
    : [{ name: currentModelName, display_name: currentModelName }, ...models];

  if (!currentModelName) return null;

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Typography variant="body2" color="text.secondary">
        {t("generative:label.sessionModel")}
      </Typography>
      <Select
        size="small"
        value={currentModelName}
        onChange={handleChange}
        disabled={saving}
        sx={{ minWidth: 200 }}
      >
        {options.map((model) => {
          // A not-downloaded model is still selectable; the chat blocks input
          // and offers the download once it becomes the session's model. Read
          // the live download state so a finished download drops the label and
          // an in-progress one keeps it despite a premature backend flag.
          const cached = getComponentDownloadState(model.name);
          const downloaded = cached?.downloaded ?? model.downloaded;
          const downloading = Boolean(cached?.downloading);
          const notDownloaded =
            Boolean(model.metadata?.requires_download) &&
            !(downloaded && !downloading) &&
            model.name !== currentModelName;
          return (
            <MenuItem key={model.name} value={model.name}>
              {model.display_name || model.name}
              {notDownloaded
                ? ` (${t("generative:label.downloadRequired")})`
                : ""}
            </MenuItem>
          );
        })}
      </Select>
    </Box>
  );
}

ModelSwitcher.propTypes = {
  sessionId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  taskName: PropTypes.string,
  currentModelName: PropTypes.string,
  onChanged: PropTypes.func,
};
