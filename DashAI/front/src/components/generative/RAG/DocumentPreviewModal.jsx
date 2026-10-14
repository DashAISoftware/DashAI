import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { createPortal } from "react-dom";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import DocumentRenderer from "../../documents/DocumentRenderer";
import {
  LoadMoreFooter,
  usePagedContent,
} from "../../documents/DocumentReader";
import { getDocument, getDocumentContent } from "../../../api/documents";
import { DOCUMENT_STATUS } from "../../../hooks/datasets/useDocuments";

function CenteredState({ children }) {
  return (
    <Box
      sx={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 2,
        p: 4,
        textAlign: "center",
      }}
    >
      {children}
    </Box>
  );
}

function DocumentPreviewBody({ dataDocument }) {
  const { t } = useTranslation(["datasets"]);
  const documentId = dataDocument.id;
  const fetchPage = useCallback(
    (contentType, offset, limit) =>
      getDocumentContent(documentId, contentType, offset, limit),
    [documentId],
  );
  const content = usePagedContent(fetchPage, "all", true);

  const isEmpty = Object.values(dataDocument.content_counts || {}).every(
    (count) => !count,
  );

  if (content.items.length === 0) {
    if (content.failed)
      return (
        <CenteredState>
          <Alert severity="error">{t("datasets:document.loadingFailed")}</Alert>
        </CenteredState>
      );
    return (
      <CenteredState>
        {isEmpty ? (
          <Typography variant="body2" color="text.secondary">
            {t("datasets:document.noContent")}
          </Typography>
        ) : (
          <CircularProgress />
        )}
      </CenteredState>
    );
  }

  return (
    <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto", p: { xs: 2, md: 4 } }}>
      <Box
        sx={{
          maxWidth: 860,
          mx: "auto",
          bgcolor: "background.box",
          borderRadius: 1,
          p: { xs: 2, md: 4 },
        }}
      >
        <DocumentRenderer
          items={content.items}
          mode="read"
          totalPages={dataDocument.total_pages}
        />
      </Box>
      {content.failed && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {t("datasets:document.loadingFailed")}
        </Alert>
      )}
      <LoadMoreFooter content={content} />
    </Box>
  );
}

export default function DocumentPreviewModal({ open, onClose, document }) {
  const { t } = useTranslation(["generative", "datasets", "common"]);
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

  const renderContent = () => {
    if (!dataDocument)
      return (
        <CenteredState>
          <CircularProgress />
        </CenteredState>
      );
    if (dataDocument.status === DOCUMENT_STATUS.ERROR)
      return (
        <CenteredState>
          <Alert severity="error">{t("datasets:document.errorMessage")}</Alert>
        </CenteredState>
      );
    if (dataDocument.status !== DOCUMENT_STATUS.FINISHED)
      return (
        <CenteredState>
          <CircularProgress />
          <Typography>{t("datasets:document.processingTitle")}</Typography>
        </CenteredState>
      );
    return (
      <DocumentPreviewBody key={dataDocument.id} dataDocument={dataDocument} />
    );
  };

  const dialogContent = (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            height: "85vh",
            bgcolor: "background.paper",
            backgroundImage: "none",
          },
        },
      }}
    >
      <DialogTitle>
        {document?.name ?? t("generative:rag.documentPreview.title")}
      </DialogTitle>
      <DialogContent
        dividers
        sx={{
          p: 0,
          display: "flex",
          flexDirection: "column",
          minHeight: 0,
          overflow: "hidden",
        }}
      >
        {renderContent()}
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

CenteredState.propTypes = {
  children: PropTypes.node,
};

DocumentPreviewBody.propTypes = {
  dataDocument: PropTypes.object.isRequired,
};

DocumentPreviewModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  document: PropTypes.object,
};
