import {
  Alert,
  Box,
  Button,
  IconButton,
  Modal,
  Typography,
} from "@mui/material";
import { Close } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

export default function DeleteConfirmationModal({
  open,
  onClose,
  onConfirm,
  content,
  warning,
  onExited,
}) {
  const { t } = useTranslation(["common"]);

  return (
    <Modal
      open={open}
      onClose={onClose}
      slotProps={{ transition: { onExited } }}
    >
      <Box
        // The modal is portaled but React still bubbles events through the
        // component tree, so without this a click inside it would reach an
        // ancestor's onClick (e.g. a clickable model row) and trigger it.
        onClick={(e) => e.stopPropagation()}
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          width: { xs: "90%", sm: 560 },
          bgcolor: "background.paper",
          borderRadius: 2,
          boxShadow: 12,
          p: 0,
          outline: "none",
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h6" component="h2">
            {t("common:confirmDeletion")}
          </Typography>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <Close />
          </IconButton>
        </Box>

        {/* Content */}
        <Box sx={{ p: 3, display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography
            variant="body1"
            sx={{ whiteSpace: "pre-line" }}
            color="text.secondary"
          >
            {content ||
              t(
                "common:confirmDeletionMessage",
                "Are you sure you want to delete this item? This action cannot be undone.",
              )}
          </Typography>
          {warning && <Alert severity="warning">{warning}</Alert>}

          {/* Footer */}
          <Box
            sx={{ display: "flex", justifyContent: "flex-end", gap: 2, mt: 1 }}
          >
            <Button onClick={onClose} sx={{ color: "text.secondary" }}>
              {t("common:cancel")}
            </Button>
            <Button onClick={onConfirm} color="error" variant="text" autoFocus>
              {t("common:delete")}
            </Button>
          </Box>
        </Box>
      </Box>
    </Modal>
  );
}
