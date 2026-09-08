import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Typography,
  Button,
  Dialog,
  IconButton,
  Tooltip,
} from "@mui/material";
import AddIcon from "@mui/icons-material/AddCircleOutline";
import ViewListIcon from "@mui/icons-material/ViewList";
import { useNavigate } from "react-router-dom";
import SearchBar from "../../threeSectionLayout/SearchBar";
import DocumentList from "./DocumentList";
import Upload from "../../shared/Upload";
import DuplicateDocumentDialog from "./DuplicateDocumentDialog";
import { useSnackbar } from "notistack";
import { getApiErrorMessage } from "../../../utils/apiError";
import {
  getSessionDocuments,
  addDocument,
  loadDocuments,
} from "../../../api/rag";

/**
 * Documents sidebar showing a searchable list of documents for the current RAG session.
 * Supports upload and navigation to the full document table view.
 *
 * @param {object}   props
 * @param {number|string} [props.selectedSessionId] - Session ID to scope documents to.
 * @param {string}   props.taskName - Task name for context (e.g. "RAGTask").
 * @param {function} [props.onDocumentChange] - Callback fired after document upload.
 * @param {boolean}  [props.showSearch=true] - Whether to show the search bar.
 * @returns {JSX.Element}
 */
export default function DocumentsBar({
  selectedSessionId,
  taskName,
  onDocumentChange,
  showSearch = true,
  indexStatus,
}) {
  const { t } = useTranslation("generative");
  const [searchQuery, setSearchQuery] = useState("");
  const [documents, setDocuments] = useState([]);
  const [filteredDocuments, setFilteredDocuments] = useState([]);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [duplicatePending, setDuplicatePending] = useState(null);
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();

  const goToDocumentsDetail = () => {
    navigate("/app/generative/rag/documents");
  };

  // Per-document chunk counts, so each row can say whether it is indexed.
  const indexStateByDocument = useMemo(() => {
    const map = {};
    (indexStatus?.documents ?? []).forEach((entry) => {
      map[entry.document_id] = entry;
    });
    return map;
  }, [indexStatus]);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        let data;
        if (selectedSessionId) {
          data = await getSessionDocuments(selectedSessionId);
        } else {
          data = await loadDocuments();
        }

        const transformedDocuments = data.map((doc) => ({
          id: doc.id,
          name: doc.file_name,
          type: doc.file_type,
          uploadedAt: doc.created,
          file_name: doc.file_name,
          file_type: doc.file_type,
          preview: doc.preview_url,
          created: doc.created,
          optional_metadata: doc.optional_metadata,
        }));

        setDocuments(transformedDocuments);
        setFilteredDocuments(transformedDocuments);
      } catch (error) {
        enqueueSnackbar(t("documentsBar.failedFetch"), {
          variant: "error",
        });
        console.error("Failed to fetch documents:", error);
      }
    };

    fetchDocuments();
  }, [selectedSessionId, enqueueSnackbar, t]);

  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredDocuments(documents);
      return;
    }

    const filtered = documents.filter((doc) =>
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()),
    );
    setFilteredDocuments(filtered);
  }, [searchQuery, documents]);

  /**
   * Handles file upload, saving each file and updating local document state immediately.
   * If a file already exists (409), pauses and asks the user for confirmation.
   * @param {File|File[]} files - File(s) to upload.
   * @param {string} [url] - Optional source URL.
   */
  const handleFileUpload = async (files, url) => {
    if (!files) return;

    const fileList = Array.isArray(files) ? files : [files];
    let uploadedCount = 0;

    for (const file of fileList) {
      try {
        const result = await addDocument({
          file,
          optional_metadata: {
            name: file.name,
            source: url || "local_upload",
          },
        });

        if (result.duplicate) {
          setDuplicatePending({
            file,
            url: url || "local_upload",
            affectedSessions: result.affectedSessions || [],
          });
          return;
        }

        const savedDoc = result.document;

        // Add to local state immediately for UI feedback
        const transformedDoc = {
          id: savedDoc.id,
          name: savedDoc.file_name,
          type: savedDoc.file_type,
          uploadedAt: savedDoc.created,
          file_name: savedDoc.file_name,
          file_type: savedDoc.file_type,
          preview: savedDoc.preview_url,
          created: savedDoc.created,
          optional_metadata: savedDoc.optional_metadata,
        };

        setDocuments((prevDocs) => [transformedDoc, ...prevDocs]);
        uploadedCount += 1;
      } catch (error) {
        // Anything other than a duplicate: tell the user which file failed and
        // why, then keep going with the rest of the selection.
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

    if (uploadedCount > 0) {
      enqueueSnackbar(
        t("documentsBar.successUpload", { count: uploadedCount }),
        { variant: "success" },
      );
      if (onDocumentChange) {
        onDocumentChange();
      }
    }
    setUploadOpen(false);
  };

  /**
   * Re-uploads the pending duplicate file with force=true after user confirmation.
   */
  const handleConfirmDuplicate = async () => {
    if (!duplicatePending) return;
    const { file, url } = duplicatePending;
    setDuplicatePending(null);
    try {
      const result = await addDocument({
        file,
        optional_metadata: { name: file.name, source: url },
        force: true,
      });
      if (!result.duplicate) {
        const savedDoc = result.document;
        const transformedDoc = {
          id: savedDoc.id,
          name: savedDoc.file_name,
          type: savedDoc.file_type,
          uploadedAt: savedDoc.created,
          file_name: savedDoc.file_name,
          file_type: savedDoc.file_type,
          preview: savedDoc.preview_url,
          created: savedDoc.created,
          optional_metadata: savedDoc.optional_metadata,
        };
        setDocuments((prevDocs) => [transformedDoc, ...prevDocs]);
        enqueueSnackbar(t("documentsBar.successUpload", { count: 1 }), {
          variant: "success",
        });
        if (onDocumentChange) {
          onDocumentChange();
        }
      }
    } catch (error) {
      enqueueSnackbar(t("documentsBar.failedUpload"), {
        variant: "error",
      });
      console.error("Failed to upload document:", error);
    } finally {
      setUploadOpen(false);
    }
  };

  const handleDetailedView = () => {
    navigate("/app/generative/rag/documents");
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        height: "100%",
        width: "100%",
        minWidth: 0, // Prevent flex shrinking issues
        maxWidth: "100%", // Ensure consistent width
      }}
    >
      <Box sx={{ p: 2, flexShrink: 0 }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Typography variant="h6">{t("documentsBar.title")}</Typography>
          <Tooltip title={t("documentsBar.detailedView")}>
            <IconButton size="small" onClick={goToDocumentsDetail}>
              <ViewListIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Typography variant="caption" sx={{ color: "text.secondary", mt: 1 }}>
          {t("documentsBar.documentCount", { count: filteredDocuments.length })}
          {selectedSessionId
            ? t("documentsBar.inCurrentSession")
            : t("documentsBar.available")}
        </Typography>
      </Box>
      {/* Add documents button - only show when no session is selected */}
      {!selectedSessionId && (
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
      )}
      {showSearch && documents.length >= 1 && (
        <Box
          sx={{ p: 2, borderBottom: 1, borderColor: "divider", flexShrink: 0 }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box sx={{ flex: 1 }}>
              <SearchBar
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onClear={() => setSearchQuery("")}
                placeholder={t("documentsBar.searchPlaceholder")}
              />
            </Box>
            {!selectedSessionId && (
              <Tooltip title={t("documentsBar.detailedView")} placement="top">
                <IconButton
                  size="medium"
                  onClick={handleDetailedView}
                  sx={{
                    color: "text.secondary",
                    "&:hover": { color: "primary.main" },
                  }}
                >
                  <ViewListIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </Box>
      )}

      <Box
        sx={{
          flex: "0 1 45vh", // Take up to 40% of viewport height, but can shrink
          overflowY: "auto",
          overflowX: "hidden",
          p: 2,
          width: "100%",
          minWidth: 0,
          maxWidth: "100%",
          minHeight: 0, // Allow shrinking when needed
        }}
      >
        {filteredDocuments.length > 0 ? (
          <DocumentList
            documents={filteredDocuments}
            indexStateByDocument={indexStateByDocument}
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
                : selectedSessionId
                  ? t("documentsBar.noDocumentsInSession")
                  : t("documentsBar.noDocumentsAvailable")}
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
            multiple={true}
            emptyUploadText={t("documentsBar.uploadDocuments")}
            sx={{ flex: 1 }}
          />
        </Box>
      </Dialog>
      <DuplicateDocumentDialog
        open={duplicatePending !== null}
        affectedSessions={duplicatePending?.affectedSessions || []}
        onCancel={() => setDuplicatePending(null)}
        onConfirm={handleConfirmDuplicate}
      />
    </Box>
  );
}
