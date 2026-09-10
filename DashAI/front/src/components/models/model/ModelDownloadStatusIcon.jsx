import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box, CircularProgress, IconButton, Tooltip } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import {
  useComponentDownloadState,
  deleteComponent,
} from "./ComponentDownloadControl";
import DeleteConfirmationModal from "../../threeSectionLayout/DeleteConfirmationModal";

/**
 * Compact, tooltip-free download status shown at the end of a model row in the
 * models side bar. The row click starts the download, so this is only an
 * indicator: a spinner while downloading, a delete icon for a downloaded model,
 * and a plain download icon otherwise.
 * @param {object} model - The model component dict.
 * @param {function} onChanged - Called after a delete so the list can refresh.
 */
export default function ModelDownloadStatusIcon({
  model,
  onChanged,
  disabled = false,
}) {
  const { t } = useTranslation(["common"]);
  const { enqueueSnackbar } = useSnackbar();
  const { downloaded, downloading } = useComponentDownloadState(model);
  const [confirmOpen, setConfirmOpen] = useState(false);

  if (!model.metadata?.requires_download) return null;

  if (downloading) {
    return <CircularProgress size={20} />;
  }

  if (downloaded) {
    return (
      <>
        <Tooltip title={t("common:componentDownload.delete")}>
          <IconButton
            size="small"
            color="error"
            aria-label={t("common:componentDownload.delete")}
            onClick={(e) => {
              e.stopPropagation();
              setConfirmOpen(true);
            }}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <DeleteConfirmationModal
          open={confirmOpen}
          onClose={() => setConfirmOpen(false)}
          onConfirm={() => {
            setConfirmOpen(false);
            deleteComponent({
              component: model,
              enqueueSnackbar,
              t,
              onStatusChange: onChanged,
            });
          }}
          content={t("common:componentDownload.confirmDelete", {
            name: model.display_name || model.name,
          })}
        />
      </>
    );
  }

  // The row click handles the download; the icon is a non-interactive hint.
  // When disabled (e.g. a credential must be authenticated first) it is greyed
  // to signal the download is not yet available.
  return (
    <Box
      component="span"
      sx={{
        display: "flex",
        alignItems: "center",
        color: disabled ? "text.disabled" : "primary.main",
        pointerEvents: "none",
      }}
    >
      <DownloadIcon fontSize="small" />
    </Box>
  );
}

ModelDownloadStatusIcon.propTypes = {
  model: PropTypes.object.isRequired,
  onChanged: PropTypes.func,
  disabled: PropTypes.bool,
};
