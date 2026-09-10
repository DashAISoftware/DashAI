import { useState } from "react";
import PropTypes from "prop-types";
import { Box, Collapse, IconButton, Typography } from "@mui/material";
import { ExpandMore, ExpandLess } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

/**
 * Collapsible panel that shows a monospaced dump of a result payload.
 * Manages its own open/closed state so it can be dropped anywhere.
 *
 * @param {object} props
 * @param {*} props.data        Object (stringified as pretty JSON) or string to show.
 * @param {object} [props.sx]   Optional MUI sx overrides for the root container.
 */
export default function TechnicalDetails({ data, sx = {} }) {
  const { t } = useTranslation(["models"]);
  const [open, setOpen] = useState(false);

  return (
    <Box sx={sx}>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          cursor: "pointer",
          color: "text.secondary",
        }}
        onClick={() => setOpen((v) => !v)}
      >
        <IconButton size="small">
          {open ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
        <Typography variant="caption">
          {t("models:label.technicalDetails")}
        </Typography>
      </Box>
      <Collapse in={open}>
        <Box
          sx={{
            bgcolor: "background.paper",
            p: 1.5,
            borderRadius: 1,
            border: "1px solid",
            borderColor: "divider",
            fontFamily: "monospace",
            fontSize: "0.75rem",
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            maxHeight: 200,
            overflow: "auto",
            mt: 1,
          }}
        >
          {typeof data === "string" ? data : JSON.stringify(data, null, 2)}
        </Box>
      </Collapse>
    </Box>
  );
}

TechnicalDetails.propTypes = {
  data: PropTypes.any,
  sx: PropTypes.object,
};
