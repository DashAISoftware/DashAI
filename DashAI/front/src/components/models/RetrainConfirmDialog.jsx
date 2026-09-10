import React from "react";
import PropTypes from "prop-types";
import {
  Modal,
  Box,
  Typography,
  IconButton,
  Button,
  Alert,
} from "@mui/material";
import {
  Close as CloseIcon,
  Warning as WarningIcon,
} from "@mui/icons-material";
import { Trans, useTranslation } from "react-i18next";

/**
 * RetrainConfirmDialog - Confirms re-training a run with existing operations
 */
export default function RetrainConfirmDialog({
  open,
  onClose,
  onConfirm,
  run,
  operationsCount,
  mode = "retrain",
}) {
  const { t } = useTranslation(["models", "common"]);

  const hasOperations =
    operationsCount &&
    (operationsCount.explainers > 0 || operationsCount.predictions > 0);

  return (
    <Modal open={open} onClose={onClose}>
      <Box
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: { xs: "90%", sm: 480 },
          bgcolor: "background.paper",
          borderRadius: 2,
          boxShadow: 12,
          p: 0,
          outline: "none",
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            {hasOperations && <WarningIcon color="warning" />}
            <Typography variant="h6" component="h2">
              {mode === "save"
                ? t("models:label.saveParameterChanges")
                : t("models:label.retrainModel")}
            </Typography>
          </Box>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <CloseIcon />
          </IconButton>
        </Box>

        {/* Content */}
        <Box sx={{ p: 3, display: "flex", flexDirection: "column", gap: 2 }}>
          {hasOperations ? (
            <>
              <Alert severity="warning">
                {mode === "save"
                  ? t("models:message.saveWillDeleteOperations")
                  : t("models:label.retrainWillDeleteOperations")}
              </Alert>
              <Typography variant="body2" color="text.secondary">
                {mode === "save" ? (
                  <Trans i18nKey="models:label.saveWillDeleteOperationsDetails">
                    Saving "<strong>{{ runName: run?.name }}</strong>" will
                    reset the run. The following will be deleted when you train
                    again:
                  </Trans>
                ) : (
                  <Trans i18nKey="models:label.retrainWillDeleteOperationsDetails">
                    Re-training run "<strong>{{ runName: run?.name }}</strong>"
                    will delete:
                  </Trans>
                )}
              </Typography>
              <Box sx={{ pl: 4 }}>
                {operationsCount.explainers > 0 && (
                  <Typography variant="body2" color="text.secondary">
                    <Trans
                      i18nKey="models:label.explainersCount"
                      count={operationsCount.explainers}
                    >
                      • <strong>{{ count: operationsCount.explainers }}</strong>{" "}
                      explainer
                    </Trans>
                  </Typography>
                )}
                {operationsCount.predictions > 0 && (
                  <Typography variant="body2" color="text.secondary">
                    <Trans
                      i18nKey="models:label.predictionsCount"
                      count={operationsCount.predictions}
                    >
                      •{" "}
                      <strong>{{ count: operationsCount.predictions }}</strong>{" "}
                      prediction
                    </Trans>
                  </Typography>
                )}
              </Box>
              <Typography variant="body2" color="text.secondary">
                {t("models:label.operationsWillBeDeletedWarning")}
              </Typography>
            </>
          ) : (
            <Typography variant="body2" color="text.secondary">
              {mode === "save" ? (
                <Trans i18nKey="models:label.saveConfirmDetails">
                  Saving "<strong>{{ runName: run?.name }}</strong>" will reset
                  its status to 'Not Started' and clear its current metrics and
                  results. Are you sure you want to continue?
                </Trans>
              ) : (
                <Trans i18nKey="models:label.retrainConfirmDetails">
                  Are you sure you want to re-train run "
                  <strong>{{ runName: run?.name }}</strong>
                  "?
                </Trans>
              )}
            </Typography>
          )}

          {/* Footer */}
          <Box
            sx={{ display: "flex", justifyContent: "flex-end", gap: 2, mt: 1 }}
          >
            <Button onClick={onClose} sx={{ color: "text.secondary" }}>
              {t("common:cancel")}
            </Button>
            <Button
              onClick={onConfirm}
              variant="contained"
              color={hasOperations ? "warning" : "primary"}
              autoFocus
            >
              {mode === "save"
                ? t("common:saveChanges")
                : hasOperations
                  ? t("models:button.deleteAndRetrain")
                  : t("models:button.retrain")}
            </Button>
          </Box>
        </Box>
      </Box>
    </Modal>
  );
}

RetrainConfirmDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  mode: PropTypes.oneOf(["retrain", "save"]),
  run: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
  }),
  operationsCount: PropTypes.shape({
    explainers: PropTypes.number,
    predictions: PropTypes.number,
  }),
};
