import { useCallback, useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  IconButton,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import LibraryAddIcon from "@mui/icons-material/LibraryAdd";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import LinkOffIcon from "@mui/icons-material/LinkOff";
import VisibilityIcon from "@mui/icons-material/Visibility";
import { useSnackbar } from "notistack";
import SearchBar from "../../threeSectionLayout/SearchBar";
import DeleteConfirmationModal from "../../threeSectionLayout/DeleteConfirmationModal";
import DocumentList from "./DocumentList";
import DocumentPreviewModal from "./DocumentPreviewModal";
import AddFromDataDialog from "./AddFromDataDialog";
import RAGDocumentUpload from "./RAGDocumentUpload";
import { getApiErrorMessage } from "../../../utils/apiError";
import {
  attachSessionDocuments,
  detachSessionDocument,
  listSessionDocuments,
} from "../../../api/rag";

function toRow(doc) {
  return {
    id: doc.id,
    name: doc.name,
    type: doc.file_type,
    file_type: doc.file_type,
    status: doc.status,
    totalPages: doc.total_pages,
    created: doc.created,
  };
}

export default function DocumentsBar({
  sessionId,
  indexStatus,
  onDocumentChange,
  showSearch = true,
}) {
  const { t } = useTranslation("generative");
  const { enqueueSnackbar } = useSnackbar();

  const [documents, setDocuments] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [pickerOpen, setPickerOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [pendingDetach, setPendingDetach] = useState(null);

  const indexStateByDocument = useMemo(() => {
    const indexing = indexStatus?.status === "indexing";
    const map = {};
    (indexStatus?.documents ?? []).forEach((entry) => {
      map[entry.document_id] = { ...entry, indexing };
    });
    return map;
  }, [indexStatus]);

  const fetchDocuments = useCallback(async () => {
    if (!sessionId) return;
    try {
      const data = await listSessionDocuments(sessionId);
      setDocuments(data.map(toRow));
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      enqueueSnackbar(t("documentsBar.failedFetch"), { variant: "error" });
    }
  }, [sessionId, enqueueSnackbar, t]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const attachedIds = useMemo(
    () => new Set(documents.map((doc) => doc.id)),
    [documents],
  );

  const filteredDocuments = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return documents;
    return documents.filter((doc) => doc.name.toLowerCase().includes(query));
  }, [documents, searchQuery]);

  const handleAttach = useCallback(
    async (documentIds) => {
      if (documentIds.length === 0) return;
      try {
        const data = await attachSessionDocuments(sessionId, documentIds);
        setDocuments(data.map(toRow));
        enqueueSnackbar(
          t("documentsBar.attached", { count: documentIds.length }),
          { variant: "success" },
        );
        onDocumentChange?.();
      } catch (error) {
        console.error("Failed to attach documents:", error);
        enqueueSnackbar(
          getApiErrorMessage(error, t("documentsBar.failedAttach")),
          { variant: "error" },
        );
      }
    },
    [sessionId, enqueueSnackbar, t, onDocumentChange],
  );

  const handleConfirmDetach = async () => {
    const doc = pendingDetach;
    setPendingDetach(null);
    if (!doc) return;
    try {
      await detachSessionDocument(sessionId, doc.id);
      setDocuments((previous) => previous.filter((row) => row.id !== doc.id));
      enqueueSnackbar(t("documentsBar.detached", { file: doc.name }), {
        variant: "success",
      });
      onDocumentChange?.();
    } catch (error) {
      console.error("Failed to detach document:", error);
      enqueueSnackbar(
        getApiErrorMessage(error, t("documentsBar.failedDetach")),
        { variant: "error" },
      );
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        height: "100%",
        width: "100%",
        minWidth: 0,
        maxWidth: "100%",
      }}
    >
      <Box sx={{ p: 2, flexShrink: 0 }}>
        <Typography variant="h6">{t("documentsBar.title")}</Typography>
        <Typography variant="caption" sx={{ color: "text.secondary", mt: 1 }}>
          {t("documentsBar.documentCount", {
            count: filteredDocuments.length,
          })}
          {t("documentsBar.inCurrentSession")}
        </Typography>
      </Box>

      <Stack direction="row" spacing={1} sx={{ flexShrink: 0, px: 2, pb: 2 }}>
        <Button
          variant="contained"
          fullWidth
          startIcon={<LibraryAddIcon />}
          onClick={() => setPickerOpen(true)}
        >
          {t("documentsBar.addFromData")}
        </Button>
        <Button
          variant="outlined"
          fullWidth
          startIcon={<UploadFileIcon />}
          onClick={() => setUploadOpen(true)}
        >
          {t("documentsBar.uploadToData")}
        </Button>
      </Stack>

      {showSearch && documents.length > 1 && (
        <Box
          sx={{
            px: 2,
            pb: 2,
            borderBottom: 1,
            borderColor: "divider",
            flexShrink: 0,
          }}
        >
          <SearchBar
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            onClear={() => setSearchQuery("")}
            placeholder={t("documentsBar.searchPlaceholder")}
          />
        </Box>
      )}

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          overflowX: "hidden",
          p: 2,
          width: "100%",
          minWidth: 0,
        }}
      >
        {filteredDocuments.length > 0 ? (
          <DocumentList
            documents={filteredDocuments}
            indexStateByDocument={indexStateByDocument}
            onDocumentClick={setPreviewDoc}
            renderActions={(doc) => (
              <>
                <Tooltip title={t("documentsBar.preview")}>
                  <IconButton
                    size="small"
                    onClick={() => setPreviewDoc(doc)}
                    aria-label={t("documentsBar.preview")}
                  >
                    <VisibilityIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={t("documentsBar.detach")}>
                  <IconButton
                    size="small"
                    onClick={() => setPendingDetach(doc)}
                    aria-label={t("documentsBar.detach")}
                  >
                    <LinkOffIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            )}
          />
        ) : (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              p: 2,
            }}
          >
            <Typography
              variant="body2"
              sx={{ color: "text.secondary", textAlign: "center" }}
            >
              {searchQuery
                ? t("documentsBar.noDocumentsFound")
                : t("documentsBar.noDocumentsInSession")}
            </Typography>
          </Box>
        )}
      </Box>

      {pickerOpen && (
        <AddFromDataDialog
          open
          onClose={() => setPickerOpen(false)}
          attachedIds={attachedIds}
          onConfirm={handleAttach}
        />
      )}

      <RAGDocumentUpload
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onReady={handleAttach}
      />

      <DocumentPreviewModal
        open={previewDoc !== null}
        onClose={() => setPreviewDoc(null)}
        document={previewDoc}
      />

      <DeleteConfirmationModal
        open={pendingDetach !== null}
        onClose={() => setPendingDetach(null)}
        onConfirm={handleConfirmDetach}
        content={pendingDetach?.name}
        warning={t("documentsBar.detachWarning")}
      />
    </Box>
  );
}

DocumentsBar.propTypes = {
  sessionId: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
    .isRequired,
  indexStatus: PropTypes.object,
  onDocumentChange: PropTypes.func,
  showSearch: PropTypes.bool,
};
