import { Box, Chip, Divider, Link, Stack, Typography } from "@mui/material";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";

const formatSize = (bytes) => {
  if (!bytes) return null;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
};

/**
 * Right panel — metadata view for a downloaded Datafile record.
 *
 * @param {object} datafile - Datafile record from the DB.
 */
export default function DatafileInfoPanel({ datafile }) {
  const { t } = useTranslation(["hub"]);
  const theme = useTheme();

  return (
    <SideBar data-tour="hub-datafile-info">
      {/* Title */}
      <Box
        sx={{
          p: 2,
          borderBottom: `1px solid ${theme.palette.ui.border}`,
          flexShrink: 0,
          height: 64,
          display: "flex",
          alignItems: "center",
        }}
      >
        <Typography variant="h6" color="text.primary">
          {t("hub:datasetDetails")}
        </Typography>
      </Box>

      {/* Content */}
      {!datafile ? (
        <Box
          sx={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            p: 3,
          }}
        >
          <Typography variant="body2" color="text.secondary" textAlign="center">
            {t("hub:selectDatasetToPreview")}
          </Typography>
        </Box>
      ) : (
        <Box sx={{ flex: 1, overflowY: "auto" }}>
          <Box
            sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}
          >
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>
              {datafile.name}
            </Typography>

            {datafile.source_url && (
              <Link
                href={datafile.source_url}
                target="_blank"
                rel="noopener noreferrer"
                variant="caption"
                sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
              >
                {t("hub:viewOnSource")} <OpenInNewIcon sx={{ fontSize: 12 }} />
              </Link>
            )}
          </Box>

          <Box sx={{ p: 2 }}>
            {datafile.description && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {datafile.description}
              </Typography>
            )}

            <Divider sx={{ mb: 1.5 }} />

            <Stack spacing={1}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  {t("hub:source")}
                </Typography>
                <Typography variant="body2">{datafile.source_name}</Typography>
              </Box>

              <Box>
                <Typography variant="caption" color="text.secondary">
                  {t("hub:size")}
                </Typography>
                <Typography variant="body2">
                  {formatSize(datafile.size_bytes) ?? t("hub:notAvailable")}
                </Typography>
              </Box>

              {datafile.tags?.length > 0 && (
                <Box>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    mb={0.5}
                  >
                    {t("hub:tags")}
                  </Typography>
                  <Stack direction="row" flexWrap="wrap" gap={0.5} useFlexGap>
                    {datafile.tags.map((tag) => (
                      <Chip
                        key={tag}
                        label={tag}
                        size="small"
                        variant="outlined"
                        sx={{
                          ...theme.typography.statusBadge,
                          border: `1px solid ${theme.palette.divider}`,
                        }}
                      />
                    ))}
                  </Stack>
                </Box>
              )}
            </Stack>
          </Box>
        </Box>
      )}
    </SideBar>
  );
}
