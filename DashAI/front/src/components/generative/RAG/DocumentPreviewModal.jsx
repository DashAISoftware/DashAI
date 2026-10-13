import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { createPortal } from "react-dom";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import DocumentView from "../../documents/DocumentView";
import { getDocument } from "../../../api/documents";

export default function DocumentPreviewModal({ open, onClose, document }) {
  const { t } = useTranslation(["generative", "common"]);
  const navigate = useNavigate();
  const [dataDocument, setDataDocument] = useState(null);

  useEffect(() => {
    if (!open || !document) {
      setDataDocument(null);
      return undefined;
    }
    let cancelled = false;
    getDocument(document.id)
      .then((loaded) => {
        if (!cancelled) setDataDocument(loaded);
      })
      .catch(() => {
        if (!cancelled) setDataDocument(null);
      });
    return () => {
      cancelled = true;
    };
  }, [open, document]);

  const openInData = () => {
    onClose();
    navigate(`/app/data/documents/${document.id}`);
  };

  const dialogContent = (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{ sx: { height: "85vh" } }}
    >
      <DialogTitle>
        {document?.name ?? t("generative:rag.documentPreview.title")}
      </DialogTitle>
      <DialogContent
        dividers
        sx={{ p: 0, display: "flex", minHeight: 0, overflow: "hidden" }}
      >
        {dataDocument && (
          <Box sx={{ flex: 1, minHeight: 0, overflow: "auto" }}>
            <DocumentView dataDocument={dataDocument} />
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button
          startIcon={<OpenInNewIcon />}
          disabled={!document}
          onClick={openInData}
        >
          {t("generative:rag.documentPreview.openInData")}
        </Button>
        <Button variant="outlined" onClick={onClose}>
          {t("common:close")}
        </Button>
      </DialogActions>
    </Dialog>
  );

  return createPortal(dialogContent, globalThis.document.body);
}

DocumentPreviewModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  document: PropTypes.object,
};
