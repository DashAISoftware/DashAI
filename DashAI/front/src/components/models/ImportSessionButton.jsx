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
import { Close as CloseIcon, FileDownload } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { useNavigate } from "react-router-dom";
import { importModelSession } from "../../api/modelSession";
import { getApiErrorMessage } from "../../utils/apiError";
import { startComponentDownload } from "./model/ComponentDownloadControl";

/**
 * Header button that imports a .dashai file as a new session.
 *
 * One modal walks through the whole import: the warning that the models
 * inside run code when used, a progress state that cannot be dismissed while
 * the request runs (it can take a while with trained models, and the app
 * navigates to the new session when it ends), and, when the import has
 * something to report, a result the user closes. An import with nothing to
 * report just closes the modal and shows a success snackbar.
 */
export default function ImportSessionButton({ onImported }) {
  const { t } = useTranslation(["models", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const inputRef = useRef(null);
  // "closed" | "warning" | "importing" | "result" | "error"
  const [phase, setPhase] = useState("closed");
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [downloadStarted, setDownloadStarted] = useState(false);

  const importing = phase === "importing";

  const displayNames = (components) =>
    components.map((component) => component.display_name).join(", ");

  const close = () => {
    if (importing) return;
    setPhase("closed");
  };

  const hasNotices = (imported) =>
    imported.warnings.length > 0 ||
    imported.recipe_runs.length > 0 ||
    imported.needs_download_trained.length > 0 ||
    imported.needs_download_untrained.length > 0;

  const handleFile = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setPhase("importing");
    try {
      const imported = await importModelSession(file);
      await onImported?.();
      navigate(`/app/models/sessions/${imported.session_id}`);
      if (hasNotices(imported)) {
        setResult(imported);
        setDownloadStarted(false);
        setPhase("result");
      } else {
        setPhase("closed");
        enqueueSnackbar(
          t("models:label.sessionImported", {
            session: imported.session_name,
            dataset: imported.dataset_name,
          }),
          { variant: "success" },
        );
      }
    } catch (error) {
      const reason = getApiErrorMessage(error);
      const message = t("models:error.importSession");
      setErrorMessage(reason ? `${message}: ${reason}` : message);
      setPhase("error");
    }
  };

  // Trained runs predict from their own saved copy, so the download only
  // matters to retrain them; untrained runs need it before anything else.
  const downloadUntrained = () => {
    setDownloadStarted(true);
    result.needs_download_untrained.forEach((component) =>
      startComponentDownload({ component, enqueueSnackbar, t }),
    );
  };

  const renderBody = () => {
    if (importing) {
      return (
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            py: 2,
          }}
        >
          <CircularProgress size={28} />
          <Box>
            <Typography>{t("models:label.importingSession")}</Typography>
            <Typography variant="body2" color="text.secondary">
              {t("models:label.importingSessionHelp")}
            </Typography>
          </Box>
        </Box>
      );
    }

    if (phase === "error") {
      return (
        <>
          <Alert severity="error">{errorMessage}</Alert>
          <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
            <Button variant="contained" onClick={close}>
              {t("common:close")}
            </Button>
          </Box>
        </>
      );
    }

    if (phase === "result" && result) {
      return (
        <>
          <Alert severity="success">
            {t("models:label.sessionImported", {
              session: result.session_name,
              dataset: result.dataset_name,
            })}
          </Alert>
          {result.warnings.map((warning) => (
            <Alert key={warning} severity="warning">
              {warning}
            </Alert>
          ))}
          {result.recipe_runs.length > 0 && (
            <Alert severity="info">
              {t("models:label.importedRecipeRuns", {
                names: result.recipe_runs.join(", "),
              })}
            </Alert>
          )}
          {result.needs_download_trained.length > 0 && (
            <Alert severity="info">
              {t("models:label.importedNeedsDownloadTrained", {
                names: displayNames(result.needs_download_trained),
              })}
            </Alert>
          )}
          {result.needs_download_untrained.length > 0 && (
            <Alert
              severity="warning"
              sx={{ "& .MuiAlert-action": { alignItems: "center", pt: 0 } }}
              action={
                <Button
                  color="inherit"
                  size="small"
                  disabled={downloadStarted}
                  onClick={downloadUntrained}
                >
                  {downloadStarted
                    ? t("common:componentDownload.downloading")
                    : t("common:componentDownload.download")}
                </Button>
              }
            >
              {t("models:label.importedNeedsDownloadUntrained", {
                names: displayNames(result.needs_download_untrained),
              })}
            </Alert>
          )}
          <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
            <Button variant="contained" onClick={close}>
              {t("models:button.gotIt")}
            </Button>
          </Box>
        </>
      );
    }

    return (
      <>
        <Alert severity="warning">
          {t("models:label.importSessionWarning")}
        </Alert>
        <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 2 }}>
          <Button onClick={close} sx={{ color: "text.secondary" }}>
            {t("common:cancel")}
          </Button>
          <Button variant="contained" onClick={() => inputRef.current?.click()}>
            {t("models:button.chooseFile")}
          </Button>
        </Box>
      </>
    );
  };

  const title =
    phase === "result"
      ? t("models:label.sessionImportedTitle")
      : t("models:button.importSession");

  return (
    <>
      <Tooltip title={t("models:button.importSession")}>
        <span>
          <IconButton
            size="small"
            disabled={importing}
            onClick={() => setPhase("warning")}
            aria-label={t("models:button.importSession")}
          >
            {importing ? (
              <CircularProgress size={16} />
            ) : (
              <FileDownload sx={{ fontSize: 18 }} />
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
      <Modal
        open={phase !== "closed"}
        onClose={close}
        disableEscapeKeyDown={importing}
      >
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
              {title}
            </Typography>
            {!importing && (
              <IconButton
                onClick={close}
                size="small"
                aria-label={t("common:close")}
                sx={{ color: "text.secondary" }}
              >
                <CloseIcon />
              </IconButton>
            )}
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
            {renderBody()}
          </Box>
        </Box>
      </Modal>
    </>
  );
}

ImportSessionButton.propTypes = {
  onImported: PropTypes.func,
};
