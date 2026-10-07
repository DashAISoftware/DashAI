import { useCallback } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Grid,
  Typography,
} from "@mui/material";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import DocumentReader from "./DocumentReader";
import { getDocumentContent, getDocumentOutline } from "../../api/documents";
import { DOCUMENT_STATUS } from "../../hooks/datasets/useDocuments";
import { formatDate } from "../../pages/results/constants/formatDate";

export default function DocumentView({ dataDocument, onNewNotebook }) {
  const { t } = useTranslation(["datasets", "common"]);
  const documentId = dataDocument?.id;
  const isFinished = dataDocument?.status === DOCUMENT_STATUS.FINISHED;
  const isError = dataDocument?.status === DOCUMENT_STATUS.ERROR;

  const fetchPage = useCallback(
    (contentType, offset, limit) =>
      getDocumentContent(documentId, contentType, offset, limit),
    [documentId],
  );
  const fetchOutline = useCallback(
    () => getDocumentOutline(documentId),
    [documentId],
  );

  if (!dataDocument) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", pt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 4, mx: 2 }}
    >
      <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
        {(isFinished || isError) && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              minHeight: "45px",
            }}
          >
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <Typography variant="h4">{dataDocument.name}</Typography>
            </Box>
          </Box>
        )}

        {(isFinished || isError) && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              mb: 2,
              flexWrap: "wrap",
            }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
              }}
            >
              <Typography variant="subtitle1" color="text.secondary">
                {[
                  formatDate(dataDocument.created),
                  dataDocument.file_name,
                  dataDocument.dataloader,
                ]
                  .filter(Boolean)
                  .join(" | ")}
              </Typography>
            </Box>

            <Box
              sx={{
                display: "flex",
                alignItems: "flex-end",
                gap: 4,
                flexDirection: "column",
              }}
            >
              <Grid
                sx={{
                  minHeight: "40px",
                  display: "flex",
                  gap: 4,
                  flexWrap: "wrap",
                  justifyContent: "flex-start",
                }}
              >
                <Button
                  variant="contained"
                  endIcon={<AddIcon />}
                  disabled={!isFinished || !onNewNotebook}
                  onClick={onNewNotebook}
                  sx={{ height: "40px" }}
                >
                  {t("datasets:button.newNotebook")}
                </Button>
              </Grid>
            </Box>
          </Box>
        )}

        {isError && (
          <Alert severity="error">{t("datasets:document.errorMessage")}</Alert>
        )}

        {!isFinished && !isError && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              minHeight: 200,
              flexDirection: "column",
              gap: 4,
            }}
          >
            <CircularProgress color="primary" />
            <Typography>{t("datasets:document.processingTitle")}</Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              textAlign="center"
            >
              {t("datasets:document.processingMessage")}
            </Typography>
          </Box>
        )}

        <DocumentReader
          enabled={isFinished}
          fetchPage={fetchPage}
          fetchOutline={fetchOutline}
          counts={dataDocument.content_counts || {}}
          totalPages={dataDocument.total_pages}
        />
      </Box>
    </Box>
  );
}

DocumentView.propTypes = {
  dataDocument: PropTypes.object,
  onNewNotebook: PropTypes.func,
};
