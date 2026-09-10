import {
  Box,
  Button,
  Dialog,
  IconButton,
  Tooltip,
  Typography,
} from "@mui/material";
import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import PropTypes from "prop-types";
import AddIcon from "@mui/icons-material/AddCircleOutline";
import { Visibility, Delete, Settings } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { getApiErrorMessage } from "../../../utils/apiError";
import { useTheme } from "@mui/material/styles";
import {
  MaterialReactTable,
  useMaterialReactTable,
  MRT_GlobalFilterTextField,
} from "material-react-table";
import { MRT_Localization_ES } from "material-react-table/locales/es";
import { MRT_Localization_EN } from "material-react-table/locales/en";
import Upload from "../../shared/Upload";
import { loadDocuments, addDocument, deleteDocument } from "../../../api/rag";
import DuplicateDocumentDialog from "./DuplicateDocumentDialog";
import { formatDate } from "../../../utils";
import { normalizeUrl } from "../../../utils/urlUtils";
import DocumentPreviewModal from "./DocumentPreviewModal";
import DocumentExtractorModal from "./DocumentExtractorModal";
import RAGSectionColumn from "../../../pages/generative/RAGSession/components/RAGSectionColumn";

/**
 * Document selection table used in the RAG setup wizard. Supports multi-select,
 * upload, delete, search, and preview of documents.
 *
 * @param {object}   props
 * @param {Array}    [props.selectedIds=[]] - Initially selected document IDs.
 * @param {function} [props.onSelect] - Callback invoked with the array of selected document objects.
 * @param {object|Array|function} [props.sx] - MUI sx prop forwarded to the container.
 * @returns {JSX.Element}
 */
export default function DocumentSelector({
  selectedIds: initialSelectedIds = [],
  onSelect,
  sx,
}) {
  const { t, i18n } = useTranslation(["generative"]);
  const { enqueueSnackbar } = useSnackbar();
  const theme = useTheme();
  const [documents, setDocuments] = useState([]);
  const [selectedIds, setSelectedIds] = useState(initialSelectedIds);
  const [isLoading, setIsLoading] = useState(true);
  const [uploadOpen, setUploadOpen] = useState(false);

  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [txtContent, setTxtContent] = useState("");

  const [extractorModalOpen, setExtractorModalOpen] = useState(false);
  const [extractorDoc, setExtractorDoc] = useState(null);

  const [duplicatePending, setDuplicatePending] = useState(null);

  const previousSelectedIdsRef = useRef(
    JSON.stringify([...initialSelectedIds].map(String).sort()),
  );

  const localization = i18n.language.startsWith("es")
    ? MRT_Localization_ES
    : MRT_Localization_EN;

  const tableData = useMemo(
    () =>
      documents.map((doc) => ({
        ...doc,
        preview: doc.preview_url,
        file_type: doc.file_name.split(".").pop().toLowerCase(),
      })),
    [documents],
  );

  const getNormalizedIdsKey = (ids) =>
    JSON.stringify([...ids].map(String).sort());

  useEffect(() => {
    const fetchDocuments = async () => {
      setIsLoading(true);
      try {
        const docs = await loadDocuments();
        const sortedDocs = docs.sort((a, b) => {
          const dateA = new Date(a.created);
          const dateB = new Date(b.created);
          return dateB - dateA;
        });
        setDocuments(sortedDocs);
      } catch (error) {
        console.error("Failed to load documents:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  useEffect(() => {
    if (
      getNormalizedIdsKey(selectedIds) !==
      getNormalizedIdsKey(initialSelectedIds)
    ) {
      setSelectedIds([...initialSelectedIds]);
    }
  }, [initialSelectedIds]);

  useEffect(() => {
    const currentKey = getNormalizedIdsKey(selectedIds);
    if (currentKey !== previousSelectedIdsRef.current) {
      const selectedIdSet = new Set(selectedIds.map(String));
      const selectedDocs = documents.filter((doc) =>
        selectedIdSet.has(String(doc.id)),
      );
      onSelect?.(selectedDocs);
      previousSelectedIdsRef.current = currentKey;
    }
  }, [selectedIds, documents, onSelect]);

  const handleToggleSelection = useCallback((id) => {
    setSelectedIds((prev) => {
      const newSelected = prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id];
      return newSelected;
    });
  }, []);

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

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setPreviewDoc(null);
    setTxtContent("");
  };

  /**
   * Merge an updated document (e.g. after extractor change) into the local
   * documents state so the table reflects the saved extractor.
   * @param {object} updatedDoc - The document returned by the update API.
   */
  const handleExtractorChanged = useCallback((updatedDoc) => {
    if (!updatedDoc) return;
    setDocuments((prev) =>
      prev.map((doc) =>
        String(doc.id) === String(updatedDoc.id)
          ? { ...doc, ...updatedDoc }
          : doc,
      ),
    );
  }, []);

  const handleSelectAll = useCallback(() => {
    setSelectedIds(documents.map((doc) => doc.id));
  }, [documents]);

  const handleDeselectAll = useCallback(() => {
    setSelectedIds([]);
  }, []);

  const handleAddDocument = useCallback(async (newDoc) => {
    try {
      return await addDocument(newDoc);
    } catch (error) {
      console.error("Failed to add document:", error);
      // Re-throw the error so the caller can handle it appropriately
      // Only 409 (duplicate) should be handled by the upload flow
      throw error;
    }
  }, []);

  /**
   * Merges uploaded documents into local state and selects them.
   * @param {object[]} docs - Documents returned by the upload API.
   */
  const applyUploadedDocuments = useCallback((docs) => {
    if (docs.length === 0) return;
    setDocuments((prev) => {
      const nextDocs = [...docs, ...prev];
      return nextDocs.filter(
        (doc, index, array) =>
          index === array.findIndex((candidate) => candidate.id === doc.id),
      );
    });
    setSelectedIds((prev) => {
      const nextSelected = new Set(prev.map(String));
      docs.forEach((doc) => nextSelected.add(String(doc.id)));
      return Array.from(nextSelected);
    });
  }, []);

  /**
   * Deletes a document from the server and removes it from local state and selection.
   * @param {number|string} id - The document ID to delete.
   */
  const handleRemoveDocument = useCallback(async (id) => {
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
      setSelectedIds((prev) => prev.filter((x) => x !== id));
    } catch (error) {
      console.error("Failed to delete document:", error);
    }
  }, []);

  /**
   * Handles multi-file upload, saving each document and updating local state.
   * If a file already exists (409), pauses and asks the user for confirmation.
   * @param {File|File[]} files - File(s) to upload.
   * @param {string} [url] - Optional source URL.
   */
  const handleFileUpload = useCallback(
    async (files, url) => {
      if (!files) return;

      const fileList = Array.isArray(files) ? files : [files];
      const uploadedDocuments = [];

      for (const file of fileList) {
        try {
          const result = await handleAddDocument({
            file,
            optional_metadata: {
              name: file.name,
              source: url || "local_upload",
            },
          });
          if (result.duplicate) {
            applyUploadedDocuments(uploadedDocuments);
            setDuplicatePending({
              file,
              url: url || "local_upload",
              affectedSessions: result.affectedSessions || [],
            });
            return;
          }
          if (result.document) {
            uploadedDocuments.push(result.document);
          }
        } catch (error) {
          // Anything other than a duplicate: tell the user which file failed
          // and why, then keep going with the rest of the selection.
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

      applyUploadedDocuments(uploadedDocuments);
      setUploadOpen(false);
    },
    [handleAddDocument, applyUploadedDocuments, enqueueSnackbar, t],
  );

  /**
   * Re-uploads the pending duplicate file with force=true after user confirmation.
   */
  const handleConfirmDuplicate = useCallback(async () => {
    if (!duplicatePending) return;
    const { file, url } = duplicatePending;
    setDuplicatePending(null);
    try {
      const result = await addDocument({
        file,
        optional_metadata: { name: file.name, source: url },
        force: true,
      });
      if (!result.duplicate && result.document) {
        applyUploadedDocuments([result.document]);
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
  }, [duplicatePending, applyUploadedDocuments, enqueueSnackbar, t]);

  const selectedIdSet = useMemo(
    () => new Set(selectedIds.map((id) => String(id))),
    [selectedIds],
  );

  const columns = useMemo(
    () => [
      {
        accessorKey: "file_name",
        header: t("generative:rag.documents.table.name"),
        size: 250,
        Cell: ({ row }) => row.original.file_name,
      },
      {
        accessorKey: "file_type",
        header: t("generative:rag.documents.table.type"),
        size: 80,
        Cell: ({ row }) => row.original.file_type?.toUpperCase() || "-",
      },
      {
        accessorKey: "created",
        header: t("generative:rag.documents.table.created"),
        size: 150,
        Cell: ({ row }) => formatDate(row.original.created) || "-",
      },
      {
        id: "actions",
        header: t("generative:rag.documents.table.actions"),
        size: 100,
        enableSorting: false,
        enableColumnFilter: false,
        muiTableHeadCellProps: {
          align: "center",
        },
        muiTableBodyCellProps: {
          align: "center",
        },
        Cell: ({ row }) => (
          <Box sx={{ display: "flex", gap: 0.5, justifyContent: "center" }}>
            <Tooltip
              title={t("generative:rag.documents.table.configureExtractor")}
            >
              <IconButton
                size="small"
                onClick={() => {
                  setExtractorDoc(row.original);
                  setExtractorModalOpen(true);
                }}
              >
                <Settings fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={t("generative:rag.documents.table.preview")}>
              <IconButton
                size="small"
                onClick={() => handleOpenPreview(row.original)}
              >
                <Visibility fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title={t("generative:rag.documents.table.delete")}>
              <IconButton
                size="small"
                onClick={() => handleRemoveDocument(row.original.id)}
                color="error"
              >
                <Delete fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        ),
      },
    ],
    [handleRemoveDocument, t],
  );

  const rowSelection = useMemo(
    () =>
      tableData.reduce((acc, doc) => {
        acc[String(doc.id)] = selectedIdSet.has(String(doc.id));
        return acc;
      }, {}),
    [tableData, selectedIdSet],
  );

  const table = useMaterialReactTable({
    columns,
    data: tableData,
    enableSelectAll: true,
    enableRowSelection: true,
    selectAllMode: "all",
    enableColumnOrdering: false,
    enableColumnActions: false,
    enableColumnHiding: true,
    enableDensityToggle: false,
    enableFullScreenToggle: false,
    enablePagination: true,
    enableBottomToolbar: true,
    enableTopToolbar: true,
    enableGlobalFilter: true,
    initialState: {
      columnVisibility: {
        file_type: false,
        created: false,
      },
      pagination: {
        pageIndex: 0,
        pageSize: 5,
      },
    },
    muiPaginationProps: {
      rowsPerPageOptions: [5, 10, 25, 50],
      showFirstButton: false,
      showLastButton: false,
    },
    muiTablePaperProps: {
      sx: {
        boxShadow: "none",
        borderRadius: 1,
        display: "flex",
        flexDirection: "column",
      },
    },
    muiTableContainerProps: {
      sx: {
        maxHeight: "none",
        flex: 1,
      },
    },
    muiTableHeadCellProps: {
      sx: {
        backgroundColor: theme.palette.action.hover,
      },
    },
    muiTableBodyCellProps: {
      sx: {
        padding: "8px 16px",
      },
    },
    muiTableBodyRowProps: ({ row }) => ({
      sx: {
        backgroundColor: selectedIdSet.has(String(row.original.id))
          ? theme.palette.action.selected
          : "inherit",
        "&:hover": {
          backgroundColor: theme.palette.action.hover,
        },
      },
    }),
    rowNumberDisplayMode: "hidden",
    renderTopToolbarCustomActions: () => (
      <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
        <MRT_GlobalFilterTextField table={table} />
      </Box>
    ),
    state: {
      rowSelection,
      isLoading,
    },
    onRowSelectionChange: (updater) => {
      const nextRowSelection =
        typeof updater === "function" ? updater(rowSelection) : updater;

      const nextSelectedIdSet = new Set(
        Object.entries(nextRowSelection)
          .filter(([, isSelected]) => Boolean(isSelected))
          .map(([rowId]) => String(rowId)),
      );

      tableData.forEach((doc) => {
        const idKey = String(doc.id);
        const wasSelected = selectedIdSet.has(idKey);
        const isSelectedNow = nextSelectedIdSet.has(idKey);
        if (wasSelected !== isSelectedNow) {
          handleToggleSelection(doc.id);
        }
      });
    },
    getRowId: (row) => String(row.id),
    localization,
  });

  return (
    <RAGSectionColumn sx={sx}>
      <Typography variant="body2" color="textSecondary">
        {t("generative:rag.setup.selectDocumentsDescription")}
      </Typography>

      <MaterialReactTable table={table} />

      <Button
        variant="contained"
        color="primary"
        size="small"
        startIcon={<AddIcon />}
        onClick={() => setUploadOpen(true)}
        sx={{ alignSelf: "flex-start", width: "fit-content" }}
      >
        {t("generative:rag.documents.uploadButton")}
      </Button>

      <Dialog
        open={uploadOpen}
        onClose={() => setUploadOpen(false)}
        maxWidth="sm"
        fullWidth
        paperProps={{
          sx: {
            maxHeight: "80vh",
            minHeight: "300px",
            display: "flex",
            flexDirection: "column",
          },
        }}
      >
        <Upload
          onFileUpload={handleFileUpload}
          multiple={true}
          emptyUploadText={t("generative:rag.documents.emptyUploadText")}
        />
      </Dialog>
      <DuplicateDocumentDialog
        open={duplicatePending !== null}
        affectedSessions={duplicatePending?.affectedSessions || []}
        onCancel={() => setDuplicatePending(null)}
        onConfirm={handleConfirmDuplicate}
      />
      <DocumentPreviewModal
        open={previewOpen}
        onClose={handleClosePreview}
        document={previewDoc}
        txtContent={txtContent}
      />
      <DocumentExtractorModal
        open={extractorModalOpen}
        onClose={() => {
          setExtractorModalOpen(false);
          setExtractorDoc(null);
        }}
        document={extractorDoc}
        onExtractorChanged={handleExtractorChanged}
      />
    </RAGSectionColumn>
  );
}

DocumentSelector.propTypes = {
  selectedIds: PropTypes.arrayOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  ),
  onSelect: PropTypes.func,
  sx: PropTypes.oneOfType([PropTypes.array, PropTypes.object, PropTypes.func]),
};
