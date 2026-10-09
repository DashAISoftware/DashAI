import { useEffect, useMemo } from "react";
import PropTypes from "prop-types";
import { Box, Divider } from "@mui/material";
import NotebookView from "../notebook/NotebookView";
import DocumentItemsPanel from "./DocumentItemsPanel";
import { useExplorersAndConverters } from "../context/ExplorersAndConvertersContext";

export default function DocumentNotebookView({ notebook }) {
  const { columnTypes, setItemSelection } = useExplorersAndConverters();

  const documentColumns = useMemo(
    () =>
      Object.fromEntries(
        Object.entries(columnTypes || {}).filter(([, info]) => info?.kinds),
      ),
    [columnTypes],
  );

  useEffect(() => () => setItemSelection(null), [setItemSelection]);

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", height: "100%" }}
      data-notebook-container
    >
      <Box sx={{ flexShrink: 0, mt: 2, mx: 2 }}>
        <DocumentItemsPanel
          notebookId={notebook.id}
          columnTypes={documentColumns}
          version={documentColumns}
          onFilterChange={setItemSelection}
        />
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box sx={{ flexGrow: 1, minHeight: 200, overflow: "auto" }}>
        <NotebookView notebook={notebook} />
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
    data_kind: PropTypes.string,
    file_path: PropTypes.string,
  }).isRequired,
};
