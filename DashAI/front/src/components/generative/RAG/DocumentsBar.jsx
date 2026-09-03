import { useCallback, useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  Dialog,
  IconButton,
  Tooltip,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/AddCircleOutline";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import TuneIcon from "@mui/icons-material/Tune";
import { useSnackbar } from "notistack";
import SearchBar from "../../threeSectionLayout/SearchBar";
import DeleteConfirmationModal from "../../threeSectionLayout/DeleteConfirmationModal";
import Upload from "../../shared/Upload";
import DocumentList from "./DocumentList";
import DocumentPreviewModal from "./DocumentPreviewModal";
import DocumentInspectorModal from "./DocumentInspectorModal";
import { getApiErrorMessage } from "../../../utils/apiError";
import { normalizeUrl } from "../../../utils/urlUtils";
import {
  addDocument,
  deleteDocument,
  getSessionDocuments,
} from "../../../api/rag";

/**
 * Shapes a document response for the list rows.
 * @param {object} doc - A document as returned by the API.
 * @returns {object} The row model.
 */
function toRow(doc) {
  return {
    id: doc.id,
    name: doc.file_name,
    type: doc.file_type,
    uploadedAt: doc.created,
    file_name: doc.file_name,
    file_type: doc.file_type,
    preview: doc.preview_url,
    created: doc.created,
    optional_metadata: doc.optional_metadata,
    // Carried so the inspector opens on the document's own extractor rather
    // than having to fetch it again.
    extractor: doc.extractor,
    default_extractor: doc.default_extractor,
  };
}

/**
 * The documents of one RAG session: add, inspect, and remove them.
 *
 * Everything the old standalone documents page could do lives here, because a
 * document now belongs to exactly one session and there is nowhere else to
 * manage it from. Reading the extracted text and choosing an extractor happen
 * in a modal: the panel is too narrow to read a document in, and the centre
 * column is deliberately reserved for the conversation.
 *
 * @param {object}   props
 * @param {number}   props.sessionId - The session whose documents these are.
 * @param {object}   [props.indexStatus] - Index state, used to badge each row
 *   with its chunk count.
 * @param {Function} [props.onDocumentChange] - Called after the set of
 *   documents changes, so the caller can re-poll the index status.
 * @param {boolean}  [props.showSearch=true] - Whether to show the search bar.
 * @returns {JSX.Element} The documents panel.
 */
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
  const [uploadOpen, setUploadOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [previewText, setPreviewText] = useState("");
  const [inspectDoc, setInspectDoc] = useState(null);
  const [pendingDelete, setPendingDelete] = useState(null);

  // Per-document chunk counts, so each row can say whether it is indexed.
  const indexStateByDocument = useMemo(() => {
    const map = {};
    (indexStatus?.documents ?? []).forEach((entry) => {
      map[entry.document_id] = entry;
    });
    return map;
  }, [indexStatus]);

  const fetchDocuments = useCallback(async () => {
    if (!sessionId) return;
    try {
      const data = await getSessionDocuments(sessionId);
      setDocuments(data.map(toRow));
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      enqueueSnackbar(t("documentsBar.failedFetch"), { variant: "error" });
    }
  }, [sessionId, enqueueSnackbar, t]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const filteredDocuments = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) return documents;
    return documents.filter((doc) => doc.name.toLowerCase().includes(query));
  }, [documents, searchQuery]);

  /**
   * Uploads the selected files into this session.
   * @param {File|File[]} files - File(s) to upload.
   * @param {string} [url] - Optional source URL.
   */
  const handleFileUpload = async (files, url) => {
    if (!files) return;
    const fileList = Array.isArray(files) ? files : [files];
    let uploaded = 0;

    for (const file of fileList) {
      try {
        const result = await addDocument({
          sessionId,
          file,
          optional_metadata: { name: file.name, source: url || "local_upload" },
        });
        if (result.duplicate) {
          // The session already holds these exact bytes, so there is nothing
          // to do and nothing to confirm.
          enqueueSnackbar(
            t("documentsBar.alreadyInSession", { file: file.name }),
            { variant: "info" },
          );
          continue;
        }
        setDocuments((previous) => [toRow(result.document), ...previous]);
        uploaded += 1;
      } catch (error) {
        // Tell the user which file failed and why, then keep going with the
        // rest of the selection.
        console.error("Upload failed:", error);
        enqueueSnackbar(
          t("documentsBar.uploadFailedReason", {
            file: file.name,
            reason: getApiErrorMessage(error, t("documentsBar.failedUpload")),
          }),
          { variant: "error" },
        );
      }
    }

    if (uploaded > 0) {
      enqueueSnackbar(t("documentsBar.successUpload", { count: uploaded }), {
        variant: "success",
      });
      onDocumentChange?.();
    }
    setUploadOpen(false);
  };

  /** Opens the plain preview, fetching the text for a txt document. */
  const handlePreview = async (doc) => {
    setPreviewText("");
    setPreviewDoc(doc);
    if (doc.file_type === "txt" && doc.preview) {
      try {
        const response = await fetch(normalizeUrl(doc.preview));
        setPreviewText(await response.text());
      } catch (error) {
        console.error("Error loading TXT:", error);
        setPreviewText(t("documentsBar.failedPreview"));
      }
    }
  };

  const handleConfirmDelete = async () => {
    const doc = pendingDelete;
    setPendingDelete(null);
    if (!doc) return;
    try {
      await deleteDocument(doc.id);
      setDocuments((previous) => previous.filter((row) => row.id !== doc.id));
      enqueueSnackbar(t("documentsBar.deleted", { file: doc.name }), {
        variant: "success",
      });
      onDocumentChange?.();
    } catch (error) {
      console.error("Failed to delete document:", error);
      enqueueSnackbar(
        getApiErrorMessage(error, t("documentsBar.failedDelete")),
        { variant: "error" },
      );
    }
  };

  /** Re-reads the list after an extractor change, and re-polls the index. */
  const handleExtractorChanged = async () => {
    await fetchDocuments();
    onDocumentChange?.();
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

      <Box sx={{ flexShrink: 0, px: 2, pb: 2 }}>
        <Button
          variant="contained"
          fullWidth
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => setUploadOpen(true)}
        >
          {t("documentsBar.addDocuments")}
        </Button>
      </Box>

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
            onDocumentClick={handlePreview}
            renderActions={(doc) => (
              <>
                <Tooltip title={t("documentsBar.inspect")}>
                  <IconButton
                    size="small"
                    onClick={() => setInspectDoc(doc)}
                    aria-label={t("documentsBar.inspect")}
                  >
                    <TuneIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title={t("documentsBar.delete")}>
                  <IconButton
                    size="small"
                    onClick={() => setPendingDelete(doc)}
                    aria-label={t("documentsBar.delete")}
                  >
                    <DeleteOutlineIcon fontSize="small" />
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

      <Dialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: {
            maxHeight: "80vh",
            minHeight: "300px",
            display: "flex",
            flexDirection: "column",
          },
        }}
      >
        <Box
          sx={{
            flex: 1,
            overflow: "auto",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Upload
            onFileUpload={handleFileUpload}
            multiple
            emptyUploadText={t("documentsBar.uploadDocuments")}
            sx={{ flex: 1 }}
          />
        </Box>
      </Dialog>

      <DocumentPreviewModal
        open={previewDoc !== null}
        onClose={() => {
          setPreviewDoc(null);
          setPreviewText("");
        }}
        document={previewDoc}
        txtContent={previewText}
      />

      <DocumentInspectorModal
        open={inspectDoc !== null}
        onClose={() => setInspectDoc(null)}
        document={inspectDoc}
        onExtractorChanged={handleExtractorChanged}
      />

      <DeleteConfirmationModal
        open={pendingDelete !== null}
        onClose={() => setPendingDelete(null)}
        onConfirm={handleConfirmDelete}
        content={pendingDelete?.name}
        warning={t("documentsBar.deleteWarning")}
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
