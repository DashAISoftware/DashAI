import PropTypes from "prop-types";
import DocumentsBar from "./DocumentsBar";
import { RAG_TASK_NAME } from "../../../api/rag";

/**
 * Unified RAG Documents Panel wrapper.
 * Handles consistent DocumentsBar rendering across all RAG contexts.
 *
 * @param {object}   props
 * @param {string}   [props.selectedSessionId] - Session ID for session-specific documents.
 * @param {object}   [props.indexStatus] - Indexing state for the session, used
 *   to badge each document with its chunk count.
 * @param {function} [props.onDocumentChange] - Optional callback for document changes.
 * @param {boolean}  [props.showSearch=false] - Whether to show the search bar.
 * @returns {JSX.Element} The DocumentsBar component.
 */
export default function RAGDocumentsPanel({
  selectedSessionId,
  indexStatus,
  onDocumentChange,
  showSearch = false,
}) {
  return (
    <DocumentsBar
      selectedSessionId={selectedSessionId}
      taskName={RAG_TASK_NAME}
      indexStatus={indexStatus}
      onDocumentChange={onDocumentChange}
      showSearch={showSearch}
    />
  );
}

RAGDocumentsPanel.propTypes = {
  selectedSessionId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  indexStatus: PropTypes.object,
  onDocumentChange: PropTypes.func,
  showSearch: PropTypes.bool,
};
