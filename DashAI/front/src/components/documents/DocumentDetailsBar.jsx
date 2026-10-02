import PropTypes from "prop-types";
import { Box, Button, Divider, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import { getDocumentSourceDownloadUrl } from "../../api/documents";
import { normalizeUrl } from "../../utils/urlUtils";

export default function DocumentDetailsBar({ dataDocument }) {
  const { t } = useTranslation(["datasets", "common"]);
  const theme = useTheme();
  const counts = dataDocument.content_counts || {};
  const params = Object.fromEntries(
    Object.entries(dataDocument.dataloader_params || {}).filter(
      ([, value]) => value !== null && value !== undefined,
    ),
  );
  const rows = [
    [t("datasets:document.fileName"), dataDocument.file_name || t("common:na")],
    [t("datasets:document.loader"), dataDocument.dataloader || t("common:na")],
    [t("datasets:document.pages"), dataDocument.total_pages ?? t("common:na")],
    [t("datasets:document.textCount"), counts.Text ?? 0],
    [t("datasets:document.imageCount"), counts.Image ?? 0],
    [
      t("datasets:document.created"),
      new Date(dataDocument.created).toLocaleString(),
    ],
  ];

  return (
    <SideBar>
      <Box
        sx={{
          p: 4,
          borderBottom: `1px solid ${theme.palette.ui.border}`,
          flexShrink: 0,
          height: 64,
          display: "flex",
          alignItems: "center",
        }}
      >
        <Typography variant="h6" color="text.primary">
          {t("datasets:document.details")}
        </Typography>
      </Box>
      <Box sx={{ flex: 1, overflowY: "auto", px: 4, py: 2 }}>
        {rows.map(([label, value]) => (
          <Box key={label} sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary">
              {label}
            </Typography>
            <Typography variant="body2">{String(value)}</Typography>
          </Box>
        ))}
        <Divider sx={{ my: 2 }} />
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          {t("datasets:document.parameters")}
        </Typography>
        {Object.entries(params).map(([key, value]) => (
          <Typography key={key} variant="body2" color="text.secondary">
            {`${key}: ${String(value)}`}
          </Typography>
        ))}
        <Button
          variant="outlined"
          size="small"
          sx={{ mt: 3 }}
          href={normalizeUrl(getDocumentSourceDownloadUrl(dataDocument.id))}
        >
          {t("datasets:document.download")}
        </Button>
      </Box>
    </SideBar>
  );
}

DocumentDetailsBar.propTypes = {
  dataDocument: PropTypes.object.isRequired,
};
