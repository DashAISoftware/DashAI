import { useCallback } from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import DocumentReader from "../../documents/DocumentReader";
import {
  getNotebookDocumentContent,
  getNotebookDocumentOutline,
} from "../../../api/notebook";
import { formatDate } from "../../../pages/results/constants/formatDate";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";

export default function DocumentNotebookView({ notebook }) {
  const { t } = useTranslation(["datasets"]);
  const { documents } = useDatasetsAndNotebooks();
  const notebookId = notebook.id;
  const sourceDocument = documents.find(
    (item) => item.id === notebook.document_id,
  );

  const fetchPage = useCallback(
    (contentType, offset, limit) =>
      getNotebookDocumentContent(notebookId, contentType, offset, limit),
    [notebookId],
  );
  const fetchOutline = useCallback(
    () => getNotebookDocumentOutline(notebookId),
    [notebookId],
  );

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 2, mt: 4, mx: 2 }}
      data-notebook-container
    >
      <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 1,
            minHeight: "45px",
          }}
        >
          <Typography variant="h4">{notebook.name}</Typography>
          <Typography variant="subtitle1" color="text.secondary">
            {[
              formatDate(notebook.created),
              sourceDocument
                ? t("datasets:documentNotebook.fromDocument", {
                    documentName: sourceDocument.name,
                  })
                : t("datasets:documentNotebook.noDocument"),
            ].join(" | ")}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t("datasets:documentNotebook.toolsComingSoon")}
          </Typography>
        </Box>

        <DocumentReader
          fetchPage={fetchPage}
          fetchOutline={fetchOutline}
          counts={sourceDocument?.content_counts || {}}
          totalPages={sourceDocument?.total_pages ?? null}
        />
      </Box>
    </Box>
  );
}

DocumentNotebookView.propTypes = {
  notebook: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string,
    created: PropTypes.string,
    document_id: PropTypes.number,
  }).isRequired,
};
