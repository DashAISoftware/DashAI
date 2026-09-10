import React from "react";
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Typography,
  Divider,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";

import { TabColumns, TabParameters } from "./tabs";
import { useTranslation } from "react-i18next";
import { formatDate } from "../../../utils";

/**
 * Read only detail view of one explorer: when it ran, which columns it used
 * and which parameters it was given. The plot and everything that acts on it
 * (edit, reset, download, fullscreen) live on the card, inside the plot's own
 * action cluster, so this modal carries no results view.
 */
export default function ExplorerInfoModal({
  open = false,
  onClose = () => {},
  explorer,
  explorerComponent,
}) {
  const { t } = useTranslation(["datasets", "common"]);

  if (!explorer) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      slotProps={{
        paper: {
          sx: {
            bgcolor: "background.paper",
            border: "1px solid",
            borderColor: "ui.border",
          },
        },
      }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 2,
          flexShrink: 0,
          bgcolor: "background.paper",
        }}
      >
        <Typography variant="h6" component="div">
          {t("datasets:label.detailsForExplorer", {
            name: explorerComponent?.display_name,
          })}
        </Typography>
        <Box sx={{ flexGrow: 1 }} />
        <IconButton onClick={onClose} aria-label={t("common:close")}>
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <Divider sx={{ flexShrink: 0 }} />

      <DialogContent sx={{ p: 5, bgcolor: "background.paper" }}>
        {/* Metadata strip */}
        {explorer.created && (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              mb: 4,
              pb: 3,
              borderBottom: "1px solid",
              borderColor: "ui.borderLight",
            }}
          >
            <Typography variant="sectionLabel" color="text.secondary">
              {t("common:created")}
            </Typography>
            <Typography variant="code" color="text.primary">
              {formatDate(explorer.created)}
            </Typography>
          </Box>
        )}

        {/* Columns + Parameters side by side */}
        <Box
          sx={{
            display: "flex",
            gap: 6,
            alignItems: "flex-start",
            flexWrap: "wrap",
          }}
        >
          <Box sx={{ flex: "1 1 240px", minWidth: 0 }}>
            <TabColumns data={explorer.columns} />
          </Box>
          <Box sx={{ flex: "1 1 240px", minWidth: 0 }}>
            <TabParameters
              data={explorer.parameters}
              schema={explorerComponent?.schema}
            />
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
