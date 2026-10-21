import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  FormControlLabel,
  IconButton,
  Modal,
  Typography,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import {
  exportModelSession,
  getSessionExportPreview,
} from "../../api/modelSession";
import { getApiErrorMessageAsync } from "../../utils/apiError";
import { triggerDownload } from "../../utils/downloadArtifact";

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );
  const value = bytes / 1024 ** exponent;
  return `${value.toFixed(exponent === 0 ? 0 : 1)} ${units[exponent]}`;
}

// Mirrors session_filename in the backend so the download keeps its name.
function sessionFilename(name) {
  const base = (name || "").replace(/[^A-Za-z0-9_-]+/g, "_");
  return `${base.replace(/^_+|_+$/g, "") || "session"}.dashai`;
}

/**
 * Choose the runs of a session and download them as a .dashai file.
 */
export default function ExportSessionDialog({ open, sessionId, onClose }) {
  const { t } = useTranslation(["models", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const [preview, setPreview] = useState(null);
  const [selected, setSelected] = useState([]);
  const [includeModels, setIncludeModels] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (!open || sessionId == null) return;
    let cancelled = false;
    setPreview(null);
    setIncludeModels(true);
    getSessionExportPreview(sessionId)
      .then((data) => {
        if (cancelled) return;
        setPreview(data);
        setSelected(
          data.runs.filter((run) => !run.in_progress).map((run) => run.id),
        );
      })
      .catch(() => {
        if (cancelled) return;
        enqueueSnackbar(t("models:error.loadExportPreview"), {
          variant: "error",
        });
        onClose();
      });
    return () => {
      cancelled = true;
    };
    // Reload only when the target changes; onClose and t do not matter here.
  }, [open, sessionId]);

  const selectableIds = (preview?.runs || [])
    .filter((run) => !run.in_progress)
    .map((run) => run.id);

  const toggle = (id) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportModelSession(sessionId, selected, includeModels);
      triggerDownload(blob, sessionFilename(preview.session_name));
      onClose();
    } catch (error) {
      const reason = await getApiErrorMessageAsync(error);
      const message = t("models:error.exportSession");
      enqueueSnackbar(reason ? `${message}: ${reason}` : message, {
        variant: "error",
      });
    } finally {
      setExporting(false);
    }
  };

  const size = preview
    ? includeModels
      ? preview.size_bytes.with_models
      : preview.size_bytes.recipe_only
    : 0;

  return (
    <Modal open={open} onClose={onClose}>
      <Box
        onClick={(e) => e.stopPropagation()}
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: { xs: "90%", sm: 520 },
          maxHeight: "85vh",
          overflowY: "auto",
          bgcolor: "background.paper",
          borderRadius: 2,
          boxShadow: 12,
          outline: "none",
        }}
      >
        <Box
          sx={{
            p: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h6" component="h2">
            {t("models:label.exportSessionTitle", {
              name: preview?.session_name || "",
            })}
          </Typography>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <CloseIcon />
          </IconButton>
        </Box>

        {!preview ? (
          <Box sx={{ p: 4, display: "flex", justifyContent: "center" }}>
            <CircularProgress size={28} />
          </Box>
        ) : (
          <Box
            sx={{
              p: 3,
              pt: 0,
              display: "flex",
              flexDirection: "column",
              gap: 2,
            }}
          >
            <Box sx={{ display: "flex", gap: 1 }}>
              <Button size="small" onClick={() => setSelected(selectableIds)}>
                {t("models:button.selectAll")}
              </Button>
              <Button size="small" onClick={() => setSelected([])}>
                {t("models:button.selectNone")}
              </Button>
            </Box>

            <Box sx={{ display: "flex", flexDirection: "column" }}>
              {preview.runs.map((run) => {
                const asRecipe = !run.with_model || !includeModels;
                const detail = run.in_progress
                  ? t("models:label.waitUntilFinished")
                  : asRecipe
                    ? t("models:label.recipeOnly")
                    : run.goal_metric_value != null
                      ? `${run.goal_metric} ${run.goal_metric_value.toFixed(3)}`
                      : "";
                return (
                  <FormControlLabel
                    key={run.id}
                    control={
                      <Checkbox
                        size="small"
                        checked={selected.includes(run.id)}
                        disabled={run.in_progress}
                        onChange={() => toggle(run.id)}
                      />
                    }
                    label={
                      <Box
                        sx={{ display: "flex", gap: 1, alignItems: "baseline" }}
                      >
                        <Typography variant="body2">{run.name}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {detail}
                        </Typography>
                      </Box>
                    }
                  />
                );
              })}
            </Box>

            <Box>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={includeModels}
                    onChange={(e) => setIncludeModels(e.target.checked)}
                  />
                }
                label={t("models:label.includeTrainedModels")}
              />
              <Typography
                variant="caption"
                color="text.secondary"
                display="block"
              >
                {t("models:label.includeTrainedModelsHelp")}
              </Typography>
            </Box>

            <Alert severity="info">
              {t("models:label.approxSize", { size: formatBytes(size) })}.{" "}
              {t("models:label.includesDataset", {
                name: preview.dataset_name,
              })}
            </Alert>

            <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 2 }}>
              <Button onClick={onClose} sx={{ color: "text.secondary" }}>
                {t("common:cancel")}
              </Button>
              <Button
                variant="contained"
                onClick={handleExport}
                disabled={selected.length === 0 || exporting}
                startIcon={
                  exporting ? (
                    <CircularProgress size={16} color="inherit" />
                  ) : null
                }
              >
                {t("common:export")}
              </Button>
            </Box>
          </Box>
        )}
      </Box>
    </Modal>
  );
}

ExportSessionDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  sessionId: PropTypes.number,
  onClose: PropTypes.func.isRequired,
};
