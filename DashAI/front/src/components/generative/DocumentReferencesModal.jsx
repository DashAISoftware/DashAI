import { useTranslation } from "react-i18next";
import {
  Box,
  Typography,
  IconButton,
  Paper,
  Stack,
  Tooltip,
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

/**
 * The chunks one document contributed to an answer.
 *
 * Wears the module's dialog treatment -- titled row with a close affordance,
 * divided body, actions along the bottom -- and lays each chunk out as a flat
 * outlined card, the same card the configuration panel uses, so a fragment
 * reads like the rest of the RAG views rather than like a bare list row.
 *
 * @param {object}   props
 * @param {boolean}  props.open - Whether the dialog is visible.
 * @param {Function} props.onClose - Closes the dialog.
 * @param {object}   [props.document] - The document the chunks came from.
 * @param {Array}    [props.chunks] - The chunks it provided.
 * @returns {JSX.Element|null} The dialog, or nothing without a document.
 */
const DocumentReferencesModal = ({ open, onClose, document, chunks }) => {
  const { t } = useTranslation(["generative", "common"]);
  if (!document || !chunks) return null;

  const getDocumentTitle = (docId, docChunks) => {
    const firstChunk = docChunks[0];
    if (firstChunk.document_title) return firstChunk.document_title;
    if (firstChunk.document_name) return firstChunk.document_name;
    if (firstChunk.title) return firstChunk.title;
    if (firstChunk.name) return firstChunk.name;
    return t("generative:documentReferences.fallbackTitle", {
      id: docId,
      defaultValue: `Document ${docId}`,
    });
  };

  const handleCopyChunk = async (chunkText) => {
    try {
      const cleanText = chunkText.replace(/\\n/g, "\n");
      await navigator.clipboard.writeText(cleanText);
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
      PaperProps={{ sx: { maxHeight: "80vh" } }}
    >
      <DialogTitle
        sx={{
          bgcolor: "background.paper",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 1,
        }}
      >
        <Stack
          direction="row"
          alignItems="center"
          spacing={1}
          sx={{ minWidth: 0 }}
        >
          <ArticleIcon color="primary" sx={{ flexShrink: 0 }} />
          <Typography variant="h6" noWrap>
            {getDocumentTitle(document.id, chunks)}
          </Typography>
        </Stack>
        <IconButton
          onClick={onClose}
          size="small"
          sx={{ color: "text.secondary" }}
          aria-label={t("common:close")}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t("generative:documentReferences.chunksCount", {
            count: chunks.length,
          })}
        </Typography>

        <Stack spacing={1}>
          {chunks.map((chunk, index) => (
            <Paper
              key={chunk.key}
              elevation={0}
              sx={{
                p: 2,
                border: 1,
                borderColor: "divider",
                bgcolor: "background.paper",
              }}
            >
              <Stack
                direction="row"
                alignItems="center"
                justifyContent="space-between"
                spacing={1}
                sx={{ mb: 1 }}
              >
                <Stack direction="row" alignItems="center" spacing={1}>
                  <Box
                    sx={{
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      backgroundColor: "primary.main",
                      flexShrink: 0,
                    }}
                  />
                  <Typography variant="subtitle2">
                    {t("generative:documentReferences.chunkLabel", {
                      position: chunk.document_position ?? index + 1,
                    })}
                  </Typography>
                </Stack>

                <Tooltip title={t("common:copy", "Copy")}>
                  <IconButton
                    size="small"
                    onClick={() => handleCopyChunk(chunk.text)}
                    aria-label={t("common:copy", "Copy")}
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
                </Tooltip>
              </Stack>

              <Typography
                variant="body2"
                sx={{ lineHeight: 1.6, whiteSpace: "pre-wrap" }}
              >
                {chunk.text.replace(/\\n/g, "\n")}
              </Typography>
            </Paper>
          ))}
        </Stack>
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
        <Button onClick={onClose} variant="outlined">
          {t("generative:documentReferences.close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DocumentReferencesModal;
