import React from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";
import DocumentListItem from "./DocumentListItem";

/**
 * Renders a vertical list of document rows.
 *
 * Purely presentational: the owner decides what a row click does and which
 * controls it offers, so one place drives both the preview and the inspector
 * instead of each list keeping its own copy of that state.
 *
 * @param {object}   props
 * @param {Array}    props.documents - Document objects to display.
 * @param {object}   [props.indexStateByDocument] - Map of document id to its
 *   indexing state, used to badge each row.
 * @param {Function} [props.onDocumentClick] - Called with the clicked document.
 * @param {Function} [props.renderActions] - Called with a document, returning
 *   the controls to reveal on hover for that row.
 * @returns {JSX.Element} The list.
 */
export default function DocumentList({
  documents,
  indexStateByDocument,
  onDocumentClick,
  renderActions,
}) {
  return (
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
          onClick={
            onDocumentClick ? () => onDocumentClick(document) : undefined
          }
          actions={renderActions?.(document)}
        />
      ))}
    </Box>
  );
}

DocumentList.propTypes = {
  documents: PropTypes.array.isRequired,
  indexStateByDocument: PropTypes.object,
  onDocumentClick: PropTypes.func,
  renderActions: PropTypes.func,
};
