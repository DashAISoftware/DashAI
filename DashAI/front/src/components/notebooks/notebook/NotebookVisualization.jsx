import React, { useState } from "react";
import { Box, CircularProgress, Divider } from "@mui/material";
import NotebookView from "./NotebookView";
import DatasetPreviewNotebook from "./DatasetPreviewNotebook";
import DocumentNotebookView from "../documentNotebook/DocumentNotebookView";

function DatasetNotebookVisualization({ notebook, existingDatasets }) {
  const [isAccordionExpanded, setIsAccordionExpanded] = useState(true);

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", height: "100%" }}
      data-notebook-container
    >
      <Box sx={{ flexGrow: 0, position: "sticky" }}>
        <DatasetPreviewNotebook
          notebook={notebook}
          existingDatasets={existingDatasets}
          onAccordionChange={setIsAccordionExpanded}
        />
      </Box>

      <Divider sx={{ my: 2, mt: 2 }} />

      <Box sx={{ flexGrow: 1, minHeight: 200, overflow: "auto" }}>
        <NotebookView notebook={notebook} />
      </Box>
    </Box>
  );
}

export default function NotebookVisualization({
  notebook,
  existingDatasets = [],
}) {
  if (!notebook) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", pt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }
  if (notebook.data_kind === "document") {
    return <DocumentNotebookView notebook={notebook} />;
  }
  return (
    <DatasetNotebookVisualization
      notebook={notebook}
      existingDatasets={existingDatasets}
    />
  );
}
