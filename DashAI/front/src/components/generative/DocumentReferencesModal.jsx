import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Box,
  Typography,
  IconButton,
  List,
  ListItem,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from "@mui/material";
import {
  Close as CloseIcon,
  Article as ArticleIcon,
  ContentCopy as CopyIcon,
} from "@mui/icons-material";

const DocumentReferencesModal = ({
  open,
  onClose,
  document,
  chunks,
  onOpenReference,
}) => {
  const { t } = useTranslation("generative");
  if (!document || !chunks) return null;

  const getDocumentTitle = (docId, chunks) => {
    const firstChunk = chunks[0];
    if (firstChunk.document_title) return firstChunk.document_title;
    if (firstChunk.document_name) return firstChunk.document_name;
    if (firstChunk.title) return firstChunk.title;
    if (firstChunk.name) return firstChunk.name;
    return t("documentReferences.fallbackTitle", {
      id: docId,
      defaultValue: `Document ${docId}`,
    });
  };

  const handleCopyChunk = async (chunkText) => {
    try {
      const cleanText = chunkText.replace(/\\n/g, "\n");
      await navigator.clipboard.writeText(cleanText);
      // You could add a toast notification here if you have a notification system
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 2,
          maxHeight: "80vh",
        },
      }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          pb: 1,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <ArticleIcon color="primary" />
          <Typography variant="h6">
            {getDocumentTitle(document.id, chunks)}
          </Typography>
        </Box>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ p: 0 }}>
        <Typography
          variant="body2"
          sx={{ p: 2, pb: 1, color: "text.secondary" }}
        >
          {t("documentReferences.chunksCount", { count: chunks.length })}
        </Typography>

        <List dense disablePadding>
          {chunks.map((chunk, index) => (
            <React.Fragment key={chunk.key}>
              <ListItem disablePadding>
                <Box sx={{ width: "100%", p: 2 }}>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      mb: 1,
                    }}
                  >
                    <Typography
                      variant="subtitle2"
                      sx={{
                        fontWeight: "bold",
                        color: "text.primary",
                        display: "flex",
                        alignItems: "center",
                        gap: 1,
                      }}
                    >
                      <Box
                        sx={{
                          width: 6,
                          height: 6,
                          borderRadius: "50%",
                          backgroundColor: "primary.main",
                          flexShrink: 0,
                        }}
                      />
                      {chunk.document_position
                        ? t("documentReferences.chunkLabel", {
                            position: chunk.document_position,
                          })
                        : t("documentReferences.chunkLabel", {
                            position: index + 1,
                          })}
                    </Typography>

                    <IconButton
                      size="small"
                      onClick={() => handleCopyChunk(chunk.text)}
                      sx={{
                        color: "text.secondary",
                        "&:hover": {
                          color: "primary.main",
                          backgroundColor: "action.hover",
                        },
                      }}
                    >
                      <CopyIcon fontSize="small" />
                    </IconButton>
                  </Box>

                  <Typography
                    variant="body2"
                    sx={{
                      color: "text.primary",
                      lineHeight: 1.6,
                      whiteSpace: "pre-wrap",
                      backgroundColor: "background.default",
                      p: 1.5,
                      borderRadius: 1,
                      border: 1,
                      borderColor: "divider",
                    }}
                  >
                    {chunk.text.replace(/\\n/g, "\n")}
                  </Typography>
                </Box>
              </ListItem>
              {index < chunks.length - 1 && <Divider variant="middle" />}
            </React.Fragment>
          ))}
        </List>
      </DialogContent>

      <DialogActions sx={{ p: 2 }}>
        <Button onClick={onClose} variant="contained">
          {t("documentReferences.close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DocumentReferencesModal;
