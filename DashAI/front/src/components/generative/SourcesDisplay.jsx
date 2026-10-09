import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Typography,
  Collapse,
  IconButton,
  List,
  ListItem,
  Divider,
  Button,
} from "@mui/material";
import {
  ExpandMore,
  ExpandLess,
  Source as SourceIcon,
  Description as DescriptionIcon,
  Visibility as VisibilityIcon,
} from "@mui/icons-material";
import DocumentReferencesModal from "./DocumentReferencesModal";

const SourcesDisplay = ({ references, onOpenReference, isUser = false }) => {
  const { t } = useTranslation("generative");
  const [expanded, setExpanded] = useState(false);
  const [documentModalOpen, setDocumentModalOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [selectedChunks, setSelectedChunks] = useState([]);
  const referenceEntries = references ? Object.entries(references) : [];
  const sourceCount = referenceEntries.length;

  const handleToggleExpanded = () => {
    setExpanded(!expanded);
  };

  const handleOpenDocumentModal = (docId, chunks) => {
    setSelectedDocument({ id: docId });
    setSelectedChunks(chunks);
    setDocumentModalOpen(true);
  };

  const handleCloseDocumentModal = () => {
    setDocumentModalOpen(false);
    setSelectedDocument(null);
    setSelectedChunks([]);
  };

  // Group references by document ID
  const groupedReferences = referenceEntries.reduce((acc, [key, ref]) => {
    const docId = ref.document_id;
    if (!acc[docId]) {
      acc[docId] = [];
    }
    acc[docId].push({ key, ...ref });
    return acc;
  }, {});

  // Get document title - fallback to "Document X" if no title available
  const getDocumentTitle = (docId, chunks) => {
    const firstChunk = chunks[0];
    if (firstChunk.document_title) return firstChunk.document_title;
    if (firstChunk.document_name) return firstChunk.document_name;
    if (firstChunk.title) return firstChunk.title;
    if (firstChunk.name) return firstChunk.name;

    return t("sourcesDisplay.fallbackTitle", {
      id: docId,
      defaultValue: `Document ${docId}`,
    });
  };

  return (
    <Box
      sx={{
        mt: 1,
        ml: isUser ? 0 : "40px",
        mr: isUser ? "40px" : 0,
        maxWidth: isUser ? "calc(80% - 40px)" : "calc(80% - 40px)",
        border: 1,
        borderColor: "divider",
        borderRadius: 1,
        backgroundColor: "background.box",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          p: 1.5,
          backgroundColor: "action.hover",
          cursor: "pointer",
        }}
        onClick={handleToggleExpanded}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <SourceIcon fontSize="small" color="primary" sx={{ flexShrink: 0 }} />
          <Typography
            variant="body2"
            sx={{ fontWeight: "medium", flexShrink: 0 }}
          >
            {t("sourcesDisplay.viewSources")}
          </Typography>
          <Box
            sx={{
              backgroundColor: "primary.main",
              color: "primary.contrastText",
              borderRadius: "10px",
              minWidth: 20,
              height: 20,
              fontSize: "0.75rem",
              fontWeight: "bold",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              px: 0.5,
              flexShrink: 0,
            }}
          >
            {sourceCount}
          </Box>
        </Box>

        <IconButton size="small">
          {expanded ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
      </Box>

      {/* Sources List */}
      <Collapse in={expanded} timeout="auto">
        <List dense disablePadding>
          {Object.entries(groupedReferences).map(
            ([docId, chunks], index, array) => (
              <React.Fragment key={docId}>
                <ListItem disablePadding>
                  <Box
                    sx={{
                      width: "100%",
                      p: 2,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      backgroundColor: "background.box",
                      gap: 2,
                    }}
                  >
                    <Box
                      sx={{
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                        minWidth: 0,
                        flex: 1,
                      }}
                    >
                      <DescriptionIcon
                        fontSize="small"
                        color="primary"
                        sx={{ flexShrink: 0 }}
                      />

                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          minWidth: 0,
                          flex: 1,
                          gap: 0.5,
                        }}
                      >
                        <Typography
                          component="span"
                          variant="body2"
                          sx={{
                            fontWeight: "bold",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                            flexShrink: 1,
                            minWidth: 0,
                          }}
                        >
                          {getDocumentTitle(docId, chunks)}
                        </Typography>
                        <Typography
                          component="span"
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            flexShrink: 0,
                            whiteSpace: "nowrap",
                          }}
                        >
                          {t("sourcesDisplay.provided")}{" "}
                          <strong>{chunks.length}</strong>{" "}
                          {t("sourcesDisplay.chunk", { count: chunks.length })}
                        </Typography>
                      </Box>
                    </Box>

                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<VisibilityIcon />}
                      onClick={() => handleOpenDocumentModal(docId, chunks)}
                      sx={{
                        fontSize: "0.75rem",
                        py: 0.5,
                        px: 1,
                        whiteSpace: "nowrap",
                        minWidth: "140px",
                        flexShrink: 0,
                      }}
                    >
                      {t("sourcesDisplay.viewChunks")}
                    </Button>
                  </Box>
                </ListItem>

                {index < array.length - 1 && <Divider />}
              </React.Fragment>
            ),
          )}
        </List>
      </Collapse>

      <DocumentReferencesModal
        open={documentModalOpen}
        onClose={handleCloseDocumentModal}
        document={selectedDocument}
        chunks={selectedChunks}
        onOpenReference={onOpenReference}
      />
    </Box>
  );
};

export default SourcesDisplay;
