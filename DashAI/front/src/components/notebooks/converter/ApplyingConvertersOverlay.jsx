import PropTypes from "prop-types";
import { Box, CircularProgress, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import { useTranslation } from "react-i18next";

export default function ApplyingConvertersOverlay({ open }) {
  const { t } = useTranslation(["datasets"]);

  if (!open) return null;

  return (
    <Box
      sx={(theme) => ({
        position: "absolute",
        inset: 0,
        zIndex: 2,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 1.5,
        bgcolor: alpha(theme.palette.background.paper, 0.8),
        backdropFilter: "blur(2px)",
        borderRadius: "inherit",
      })}
    >
      <CircularProgress size={28} />
      <Typography variant="body2" color="text.secondary">
        {t("datasets:label.applyingConverters")}
      </Typography>
    </Box>
  );
}

ApplyingConvertersOverlay.propTypes = {
  open: PropTypes.bool.isRequired,
};
