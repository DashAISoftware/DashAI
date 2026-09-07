import React, { useState } from "react";
import Dialog from "@mui/material/Dialog";
import Upload from "../../shared/Upload";
import { addDocument } from "../../../api/rag";
import DuplicateDocumentDialog from "./DuplicateDocumentDialog";
import AddIcon from "@mui/icons-material/AddCircleOutline";
import {
  Paper,
  Typography,
  IconButton,
  Tooltip,
  LinearProgress,
  Button,
  Grid,
} from "@mui/material";
import PropTypes from "prop-types";
import { DataGrid } from "@mui/x-data-grid";
import VisibilityIcon from "@mui/icons-material/Visibility";
import SettingsIcon from "@mui/icons-material/Settings";
import { formatDate } from "../../../utils";
import DeleteItemModal from "../../custom/DeleteItemModal";
import DocumentPreviewModal from "./DocumentPreviewModal";
import DocumentExtractorModal from "./DocumentExtractorModal";
import { normalizeUrl } from "../../../utils/urlUtils";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { getApiErrorMessage } from "../../../utils/apiError";

/**
 * DataGrid table listing documents with preview, deletion, and upload actions.
 *
 * @param {object}   props
 * @param {Array}    props.documents - Array of document objects.
 * @param {function} props.onRemove - Callback invoked with document ID when deleting.
 * @param {function} [props.onAddDocument] - Callback invoked with the saved document after upload.
 * @param {function} [props.onSelectDocument] - Callback invoked with the selected row when a row is clicked.
 * @param {boolean}  [props.isLoading=false] - Whether the data is still loading.
 * @param {string}   [props.tableTitle=null] - Custom table title (shown when showTableTitle is true).
 * @param {boolean}  [props.showTableTitle=false] - Whether to show the table title header.
 * @returns {JSX.Element}
 */
export default function DocumentTable({
  documents,
  onRemove,
  onAddDocument,
  onSelectDocument = null,
  onExtractorChanged = null,
  isLoading = false,
  tableTitle = null,
  showTableTitle = false,
}) {
  const { t } = useTranslation(["generative", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [txtContent, setTxtContent] = useState("");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [extractorModalOpen, setExtractorModalOpen] = useState(false);
  const [extractorDoc, setExtractorDoc] = useState(null);
  const [duplicatePending, setDuplicatePending] = useState(null);

  /**
   * Opens the document preview modal, fetching TXT content if applicable.
   * @param {object} doc - The document to preview.
   */
  const handleOpenPreview = async (doc) => {
    setPreviewDoc(doc);
    if (doc.file_type === "txt" && doc.preview) {
      try {
        const res = await fetch(normalizeUrl(doc.preview));
        const text = await res.text();
        setTxtContent(text);
      } catch (e) {
        setTxtContent("Error loading TXT file");
      }
    }
    setPreviewOpen(true);
  };

  const handleRemoveDocument = (id) => {
    if (onRemove) onRemove(id);
  };

  /**
   * Handles file upload from the Upload component, saving each file via the API.
   * If a file already exists (409), pauses and asks the user for confirmation.
   * @param {File|File[]} files - File(s) to upload.
   * @param {string} [url] - Optional source URL.
   */
  const handleFileUpload = async (files, url) => {
    if (!files) return;
    const fileList = Array.isArray(files) ? files : [files];
    for (const file of fileList) {
      const docToAdd = {
        file,
        optional_metadata: {
          name: file.name,
          source: url || "local_upload",
        },
      };
      try {
        const result = await addDocument(docToAdd);
        if (result.duplicate) {
          setDuplicatePending({
            file,
            url: url || "local_upload",
            affectedSessions: result.affectedSessions || [],
          });
          return;
        }
        if (onAddDocument) onAddDocument(result.document);
      } catch (error) {
        // Anything other than a duplicate: tell the user which file failed and
        // why, then keep going with the rest of the selection.
        console.error("Upload failed:", error);
        enqueueSnackbar(
          t("generative:rag.documents.uploadFailedReason", {
            file: file.name,
            reason: getApiErrorMessage(
              error,
              t("generative:rag.documents.uploadFailed"),
            ),
          }),
          { variant: "error" },
        );
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
      if (!result.duplicate && onAddDocument) {
        onAddDocument(result.document);
      }
    } catch (error) {
      console.error("Forced upload failed:", error);
      enqueueSnackbar(
        t("generative:rag.documents.uploadFailedReason", {
          file: file.name,
          reason: getApiErrorMessage(
            error,
            t("generative:rag.documents.uploadFailed"),
          ),
        }),
        { variant: "error" },
      );
    }
    setUploadOpen(false);
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setPreviewDoc(null);
    setTxtContent("");
  };

  const columns = [
    {
      field: "id",
      headerName: t("generative:rag.documents.table.id"),
      flex: 0.1,
      editable: false,
    },
    {
      field: "file_name",
      headerName: t("generative:rag.documents.table.name"),
      flex: 0.6,
      editable: false,
    },
    {
      field: "created",
      headerName: t("generative:rag.documents.table.created"),
      flex: 0.4,
      editable: false,
      valueGetter: (value) => formatDate(value),
    },
    {
      field: "last_modified",
      headerName: t("generative:rag.documents.table.lastModified"),
      flex: 0.4,
      editable: false,
      valueGetter: (value, row) => {
        return row?.optional_metadata?.last_modified
          ? formatDate(row.optional_metadata.last_modified)
          : t("common:na");
      },
    },
    {
      field: "extractor",
      headerName: t("generative:rag.documents.table.extractor"),
      flex: 0.3,
      editable: false,
      valueGetter: (value, row) => row?.extractor?.component,
    },
    {
      field: "actions",
      type: "actions",
      headerName: t("generative:rag.documents.table.actions"),
      flex: 0.3,
      getActions: (params) => [
        <Tooltip
          title={t("generative:rag.documents.table.configureExtractor")}
          key="extractor"
        >
          <IconButton
            size="small"
            onClick={() => {
              setExtractorDoc(params.row);
              setExtractorModalOpen(true);
            }}
          >
            <SettingsIcon fontSize="small" />
          </IconButton>
        </Tooltip>,
        <Tooltip
          title={t("generative:rag.documents.table.preview")}
          key="preview"
        >
          <IconButton
            size="small"
            onClick={() => handleOpenPreview(params.row)}
          >
            <VisibilityIcon fontSize="small" />
          </IconButton>
        </Tooltip>,
        <DeleteItemModal
          key="delete-button"
          deleteFromTable={() => handleRemoveDocument(params.row.id)}
          item="document"
        />,
      ],
    },
  ];

  return (
    <Paper sx={{ py: 4, px: 4 }}>
      {showTableTitle ? (
        <Grid
          container
          justifyContent="space-between"
          alignItems="center"
          sx={{ mb: 4 }}
        >
          <Typography variant="h5" component="h2">
            {tableTitle || t("generative:rag.documents.table.currentDocuments")}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={() => setUploadOpen(true)}
          >
            {t("generative:rag.documents.table.addDocument")}
          </Button>
        </Grid>
      ) : (
        <Grid
          container
          justifyContent="flex-end"
          alignItems="center"
          sx={{ mb: 4 }}
        >
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={() => setUploadOpen(true)}
          >
            {t("generative:rag.documents.table.addDocument")}
          </Button>
        </Grid>
      )}
      {documents.length === 0 && !isLoading ? (
        <Typography
          variant="body1"
          color="warning.main"
          textAlign="center"
          mt={16}
          mx={"auto "}
        >
          {t("generative:rag.documents.table.noDocumentsAvailable")}
        </Typography>
      ) : (
        <DataGrid
          rows={documents}
          columns={columns}
          initialState={{
            pagination: { paginationModel: { pageSize: 5 } },
          }}
          pageSizeOptions={[5, 10]}
          disableRowSelectionOnClick
          onRowClick={(params) => {
            if (onSelectDocument) {
              onSelectDocument(params.row);
            }
          }}
          autoHeight
          loading={isLoading}
          slots={{
            loadingOverlay: LinearProgress,
          }}
          getRowId={(row) => row.id}
          sx={{
            "& .MuiDataGrid-cell:focus": { outline: "none" },
            minHeight: 300,
          }}
        />
      )}
      <DocumentPreviewModal
        open={previewOpen}
        onClose={handleClosePreview}
        document={previewDoc}
        txtContent={txtContent}
      />
      {extractorDoc && (
        <DocumentExtractorModal
          open={extractorModalOpen}
          onClose={() => {
            setExtractorModalOpen(false);
            setExtractorDoc(null);
          }}
          document={extractorDoc}
          onExtractorChanged={(updatedDoc) => {
            if (onExtractorChanged) onExtractorChanged();
            setExtractorModalOpen(false);
            setExtractorDoc(null);
          }}
        />
      )}
      <Dialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <Upload
          onFileUpload={handleFileUpload}
          multiple={true}
          emptyUploadText={t("generative:rag.documents.table.emptyUploadText")}
        />
      </Dialog>
      <DuplicateDocumentDialog
        open={duplicatePending !== null}
        affectedSessions={duplicatePending?.affectedSessions || []}
        onCancel={() => setDuplicatePending(null)}
        onConfirm={handleConfirmDuplicate}
      />
    </Paper>
  );
}

DocumentTable.propTypes = {
  documents: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      createdAt: PropTypes.string.isRequired,
      preview: PropTypes.string,
    }),
  ).isRequired,
  onRemove: PropTypes.func.isRequired,
  onSelectDocument: PropTypes.func,
  onExtractorChanged: PropTypes.func,
  isLoading: PropTypes.bool,
  tableTitle: PropTypes.string,
  showTableTitle: PropTypes.bool,
};
