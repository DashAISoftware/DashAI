import React, { useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  IconButton,
  Modal,
  Tooltip,
  Typography,
} from "@mui/material";
import { Close as CloseIcon, FileUpload } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router-dom";
import { importModelSession } from "../../api/modelSession";
import { getApiErrorMessage } from "../../utils/apiError";

/**
 * Header button that imports a .dashai file as a new session, after warning
 * that the models inside run code when used.
 */
export default function ImportSessionButton({ onImported }) {
  const { t } = useTranslation(["models", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [warningOpen, setWarningOpen] = useState(false);
  const [importing, setImporting] = useState(false);

  const handleFile = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setWarningOpen(false);
    setImporting(true);
    try {
      const result = await importModelSession(file);
      await onImported?.();
      navigate(`/app/models/sessions/${result.session_id}`);
      enqueueSnackbar(
        t("models:label.sessionImported", {
          session: result.session_name,
          dataset: result.dataset_name,
        }),
        { variant: "success" },
      );
      result.warnings.forEach((warning) =>
        enqueueSnackbar(warning, { variant: "warning" }),
      );
      if (result.recipe_runs.length) {
        enqueueSnackbar(
          t("models:label.importedRecipeRuns", {
            names: result.recipe_runs.join(", "),
          }),
          { variant: "info" },
        );
      }
    } catch (error) {
      const reason = getApiErrorMessage(error);
      const message = t("models:error.importSession");
      enqueueSnackbar(reason ? `${message}: ${reason}` : message, {
        variant: "error",
      });
    } finally {
      setImporting(false);
    }
  };

  return (
    <>
      <Tooltip title={t("models:button.importSession")}>
        <span>
          <IconButton
            size="small"
            disabled={importing}
            onClick={() => setWarningOpen(true)}
            aria-label={t("models:button.importSession")}
          >
            {importing ? (
              <CircularProgress size={16} />
            ) : (
              <FileUpload sx={{ fontSize: 18 }} />
            )}
          </IconButton>
        </span>
      </Tooltip>
      <input
        ref={inputRef}
        type="file"
        accept=".dashai"
        hidden
        onChange={handleFile}
      />
      <Modal open={warningOpen} onClose={() => setWarningOpen(false)}>
        <Box
          onClick={(e) => e.stopPropagation()}
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: { xs: "90%", sm: 480 },
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
              {t("models:button.importSession")}
            </Typography>
            <IconButton
              onClick={() => setWarningOpen(false)}
              size="small"
              sx={{ color: "text.secondary" }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
          <Box
            sx={{
              p: 3,
              pt: 0,
              display: "flex",
              flexDirection: "column",
              gap: 2,
            }}
          >
            <Alert severity="warning">
              {t("models:label.importSessionWarning")}
            </Alert>
            <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 2 }}>
              <Button
                onClick={() => setWarningOpen(false)}
                sx={{ color: "text.secondary" }}
              >
                {t("common:cancel")}
              </Button>
              <Button
                variant="contained"
                onClick={() => inputRef.current?.click()}
              >
                {t("models:button.chooseFile")}
              </Button>
            </Box>
          </Box>
        </Box>
      </Modal>
    </>
  );
}

ImportSessionButton.propTypes = {
  onImported: PropTypes.func,
};
