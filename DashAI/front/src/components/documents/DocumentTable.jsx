import React, { useEffect, useState, useCallback } from "react";
import { DataGrid, GridToolbar } from "@mui/x-data-grid";
import { useSnackbar } from "notistack";
import {
  Button,
  Grid,
  Paper,
  Typography,
  LinearProgress,
  Box,
} from "@mui/material";
import {
  get_documents_json,
  delete_document as deleteDocumentRequest,
} from "../../api/documents";
import {
  AddCircleOutline as AddIcon,
  Update as UpdateIcon,
} from "@mui/icons-material";
import DeleteItemModal from "../custom/DeleteItemModal";
import DocumentSummaryModal from "./DocumentSummaryModal";

function DocumentTable({
  handleNewDocument,
  updateTableFlag,
  setUpdateTableFlag,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [selectionModel, setSelectionModel] = useState([]);

  const getDocuments = useCallback(async () => {
    setLoading(true);
    try {
      const docs = await get_documents_json();
      setDocuments(docs);
    } catch (error) {
      enqueueSnackbar("Error when trying to get the documents", {
        variant: "error",
      });
      console.error("Error fetching documents:", error);
    } finally {
      setLoading(false);
    }
  }, [enqueueSnackbar]);

  const deleteDocument = async (doc_name) => {
    try {
      await deleteDocumentRequest(doc_name);
      setUpdateTableFlag(true);
      enqueueSnackbar("Document successfully deleted.", {
        variant: "success",
      });
    } catch (error) {
      enqueueSnackbar("Error when trying to delete the document", {
        variant: "error",
      });
      console.error("Error deleting document:", error);
    }
  };

  const createDeleteHandler = useCallback(
    (doc_name) => () => {
      deleteDocument(doc_name);
    },
    [deleteDocument],
  );

  useEffect(() => {
    getDocuments();
  }, [getDocuments]);

  useEffect(() => {
    if (updateTableFlag) {
      getDocuments();
      setUpdateTableFlag(false);
    }
  }, [updateTableFlag, setUpdateTableFlag, getDocuments]);

  const columns = React.useMemo(
    () => [
      {
        field: "id",
        headerName: "ID",
        minWidth: 30,
        editable: false,
      },
      {
        field: "doc_name",
        headerName: "Document Name",
        minWidth: 200,
        editable: false,
      },
      {
        field: "created_at",
        headerName: "Created At",
        minWidth: 200,
        editable: false,
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 150,
        getActions: (params) => [
          <DeleteItemModal
            key="delete-component"
            deleteFromTable={createDeleteHandler(params.row.doc_name)}
          />,
          <DocumentSummaryModal
            key="summary-component"
            docName={params.row.doc_name}
          />,
        ],
      },
    ],
    [createDeleteHandler],
  );

  return (
    <Paper
      sx={{
        py: 4,
        px: 6,
        height: "100%",
        minHeight: 400,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Grid
        container
        direction="row"
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 4 }}
      >
        <Typography variant="h5" component="h2">
          Current documents
        </Typography>
        <Grid item>
          <Grid container spacing={2}>
            <Grid item>
              <Button
                variant="contained"
                onClick={handleNewDocument}
                endIcon={<AddIcon />}
              >
                New Document
              </Button>
            </Grid>
            <Grid item>
              <Button
                variant="contained"
                onClick={() => setUpdateTableFlag(true)}
                endIcon={<UpdateIcon />}
                disabled={loading}
              >
                Update
              </Button>
            </Grid>
          </Grid>
        </Grid>
      </Grid>

      <Box
        sx={{
          flex: 1,
          minHeight: 300,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {!loading && documents.length === 0 ? (
          <Box
            sx={{
              flex: 1,
              minHeight: 300,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
            }}
          >
            <Typography
              variant="h6"
              color="text.secondary"
              align="center"
              sx={{ width: "100%" }}
            >
              No documents available
            </Typography>
          </Box>
        ) : (
          <DataGrid
            rows={documents}
            columns={columns}
            initialState={{
              pagination: {
                paginationModel: {
                  pageSize: 5,
                },
              },
            }}
            getRowId={(row) => String(row.id)}
            pageSize={5}
            sortModel={[{ field: "id", sort: "asc" }]}
            pageSizeOptions={[5, 10]}
            checkboxSelection
            selectionModel={selectionModel}
            onSelectionModelChange={setSelectionModel}
            disableRowSelectionOnClick={false}
            autoHeight={false}
            loading={loading}
            slots={{
              toolbar: GridToolbar,
              loadingOverlay: LinearProgress,
            }}
            sx={{
              flex: 1,
              minHeight: 300,
              "& .MuiDataGrid-cell:focus": {
                outline: "none",
              },
            }}
          />
        )}
      </Box>
    </Paper>
  );
}

export default DocumentTable;
