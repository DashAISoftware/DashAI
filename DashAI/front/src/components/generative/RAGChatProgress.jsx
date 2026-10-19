import {
  Box,
  CircularProgress,
  Paper,
  Typography,
  useTheme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { ChatAvatar } from "./ChatAvatar";
import { resolveRAGProgressText } from "./utils";

/**
 * Live status line for an in-flight RAG answer.
 *
 * Renders the current RAG pipeline stage reported on `process.progress` while
 * the answer is still being produced. The payload is resolved through
 * `resolveRAGProgressText`, so anything null or unrecognized renders nothing
 * and the parent falls back to the generic waiting bubble. Once the final
 * answer (or an error) arrives the backend resets `progress` to null and the
 * parent's finished branch replaces this component, so there is no extra
 * hiding logic here.
 *
 * @param {object} props
 * @param {{ stage?: string, queries?: string[] }|null} [props.progress] - The
 *   live process progress payload.
 * @returns {JSX.Element|null} The status row, or null when no status applies.
 */
export default function RAGChatProgress({ progress }) {
  const theme = useTheme();
  const { t } = useTranslation(["generative", "common"]);

  const resolved = resolveRAGProgressText(progress);
  if (!resolved) return null;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        alignItems: "flex-start",
        justifyContent: "flex-start",
        mb: 4,
        width: "100%",
      }}
    >
      <ChatAvatar isUser={false} />

      <Box sx={{ maxWidth: "80%" }}>
        <Typography
          variant="body2"
          component="span"
          sx={{
            ml: 2,
            mb: 1,
            display: "block",
            color: "text.secondary",
          }}
        >
          {t("common:model")}
        </Typography>

        {/* role="status" + aria-live: the text changes while the answer is
            being produced, so assistive tech should announce each stage. */}
        <Paper
          role="status"
          aria-live="polite"
          sx={{
            backgroundColor: theme.palette.ui.box,
            color: "text.primary",
            padding: theme.spacing(1.5, 4),
            maxWidth: "100%",
            borderRadius: 2,
            borderTopLeftRadius: 0,
            display: "flex",
            alignItems: "center",
            gap: 1.5,
          }}
        >
          <CircularProgress size={16} aria-hidden={true} />
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ overflowWrap: "anywhere" }}
          >
            {t(resolved.key, resolved.values)}
          </Typography>
        </Paper>
      </Box>
    </Box>
  );
}
