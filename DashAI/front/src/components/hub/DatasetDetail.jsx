import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Link,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import CloudDownloadIcon from "@mui/icons-material/CloudDownload";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import AddIcon from "@mui/icons-material/Add";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { getDatasetInfo } from "../../api/hub";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import LoadingDots from "../shared/LoadingDots";

/**
 * Right panel — detailed view of a selected Hub dataset with action buttons.
 *
 * @param {object|null} dataset - Selected DatasetEntry, or null if none.
 * @param {string|null} sourceName - Active DatasetSource class name.
 * @param {object|null} download - Datafile record for this dataset (if any).
 * @param {boolean} downloadLoading - True while the download record is being created.
 * @param {function} onStartDownload - Called when user clicks "Download to DashAI".
 * @param {function} onStartImport - Called when download is ready and user clicks "Add to DashAI".
 */
export default function DatasetDetail({
  dataset,
  sourceName,
  download = null,
  downloadLoading = false,
  onStartDownload,
  onStartImport,
}) {
  const { t } = useTranslation(["hub"]);
  const theme = useTheme();
  const [extraInfo, setExtraInfo] = useState(null);
  const [infoLoading, setInfoLoading] = useState(false);

  const formatSize = (bytes) => {
    if (!bytes) return null;
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
    return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  };

  useEffect(() => {
    if (!dataset || !sourceName) {
      setExtraInfo(null);
      setInfoLoading(false);
      return;
    }
    setExtraInfo(null);
    setInfoLoading(true);
    getDatasetInfo(sourceName, dataset.id)
      .then((info) => setExtraInfo(info))
      .catch(() => setExtraInfo({}))
      .finally(() => setInfoLoading(false));
  }, [dataset?.id, sourceName]);

  const renderActionButton = () => {
    if (downloadLoading) {
      return (
        <Button
          variant="contained"
          size="small"
          disabled
          startIcon={<CircularProgress size={14} />}
        >
          {t("hub:startingDownload")}
        </Button>
      );
    }

    if (!download) {
      return (
        <Button
          variant="contained"
          size="small"
          startIcon={<CloudDownloadIcon />}
          onClick={() => onStartDownload?.()}
        >
          {t("hub:downloadToDashAI")}
        </Button>
      );
    }

    if (download.status === "downloading") {
      return (
        <Button
          variant="contained"
          size="small"
          disabled
          startIcon={<CircularProgress size={14} />}
        >
          {t("hub:downloading")}
        </Button>
      );
    }

    if (download.status === "error") {
      return (
        <Stack direction="row" spacing={1}>
          <Tooltip title={download.error_message || t("hub:downloadError")}>
            <Button
              variant="outlined"
              size="small"
              color="error"
              startIcon={<ErrorIcon />}
              disabled
            >
              {t("hub:downloadFailed")}
            </Button>
          </Tooltip>
          <Button
            variant="outlined"
            size="small"
            startIcon={<CloudDownloadIcon />}
            onClick={() => onStartDownload?.()}
          >
            {t("hub:retry")}
          </Button>
        </Stack>
      );
    }

    // READY
    return (
      <Button
        variant="contained"
        size="small"
        startIcon={<AddIcon />}
        onClick={() => onStartImport?.()}
      >
        {t("hub:addToDashAI")}
      </Button>
    );
  };

  return (
    <SideBar>
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
      {!dataset ? (
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
              {dataset.name}
            </Typography>

            <Stack
              data-tour="hub-dataset-add"
              direction="row"
              spacing={1}
              mb={1.5}
              flexWrap="wrap"
              useFlexGap
            >
              <Box data-tour="hub-dataset-action" sx={{ display: "flex" }}>
                {renderActionButton()}
              </Box>
              {download?.status === "ready" && (
                <Chip
                  icon={<CheckCircleIcon />}
                  label={t("hub:downloaded")}
                  size="small"
                  color="success"
                  variant="outlined"
                />
              )}
            </Stack>

            <Link
              href={dataset.url}
              target="_blank"
              rel="noopener noreferrer"
              variant="caption"
              sx={{ display: "flex", alignItems: "center", gap: 0.5 }}
            >
              {t("hub:viewOnSource")} <OpenInNewIcon sx={{ fontSize: 12 }} />
            </Link>
          </Box>

          <Box sx={{ p: 2 }}>
            {(extraInfo?.description || dataset.description) && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {extraInfo?.description || dataset.description}
              </Typography>
            )}

            <Divider sx={{ mb: 1.5 }} />

            <Stack spacing={1}>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  {t("hub:size")}
                </Typography>
                <Typography variant="body2">
                  {infoLoading ? (
                    <LoadingDots />
                  ) : (extraInfo?.size_bytes ?? dataset.size_bytes) != null ? (
                    formatSize(extraInfo?.size_bytes ?? dataset.size_bytes)
                  ) : (
                    t("hub:notAvailable")
                  )}
                </Typography>
              </Box>

              {(extraInfo?.tags ?? dataset.tags)?.length > 0 && (
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
                    {(extraInfo?.tags ?? dataset.tags).map((tag) => (
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
