import React, { useState } from "react";
import { Box } from "@mui/material";
import DocumentListItem from "./DocumentListItem";
import DocumentPreviewModal from "./DocumentPreviewModal";
import { normalizeUrl } from "../../../utils/urlUtils";

/**
 * Renders a vertical list of document items with preview-on-click capability.
 *
 * @param {object} props
 * @param {Array}  props.documents - Array of document objects to display.
 * @param {object} [props.indexStateByDocument] - Map of document id to its
 *   indexing state, used to badge each row.
 * @returns {JSX.Element}
 */
export default function DocumentList({ documents, indexStateByDocument }) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [txtContent, setTxtContent] = useState("");

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
        console.error("Error loading TXT:", e);
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

  return (
    <>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 1.5,
          width: "100%",
          minWidth: 0,
          maxWidth: "100%",
        }}
      >
        {documents.map((document) => (
          <DocumentListItem
            key={document.id}
            document={document}
            disabled={false}
            indexState={indexStateByDocument?.[document.id]}
            onClick={() => handleOpenPreview(document)}
          />
        ))}
      </Box>
      <DocumentPreviewModal
        open={previewOpen}
        onClose={handleClosePreview}
        document={previewDoc}
        txtContent={txtContent}
      />
    </>
  );
}
