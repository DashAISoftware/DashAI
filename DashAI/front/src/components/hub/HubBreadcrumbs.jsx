import Breadcrumbs from "@mui/material/Breadcrumbs";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import IconButton from "@mui/material/IconButton";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import Box from "@mui/material/Box";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

/**
 * Breadcrumbs for the Hub module.
 *
 * @param {string} [sourceDisplayName] - Simple mode: human-readable source name (current crumb).
 * @param {Array<{label: string, onClick?: function}>} [crumbs] - Full mode: explicit crumb list.
 *   Last entry without onClick renders as plain text (current page); others render as links.
 * @param {function} [onBack] - Custom back-button handler. Defaults to navigating to /app/data/hub.
 */
export default function HubBreadcrumbs({ sourceDisplayName, crumbs, onBack }) {
  const navigate = useNavigate();
  const { t } = useTranslation(["hub", "common"]);

  const datasetsRootCrumb = {
    label: t("common:data"),
    onClick: () => navigate("/app/data"),
  };
  const hubLinkCrumb = {
    label: t("hub:title"),
    onClick: () => navigate("/app/data/hub"),
  };
  const hubCurrentCrumb = { label: t("hub:title") };

  let resolvedCrumbs;
  if (crumbs) {
    resolvedCrumbs = [datasetsRootCrumb, hubLinkCrumb, ...crumbs.slice(1)];
  } else if (sourceDisplayName) {
    resolvedCrumbs = [
      datasetsRootCrumb,
      hubLinkCrumb,
      { label: sourceDisplayName },
    ];
  } else {
    resolvedCrumbs = [datasetsRootCrumb, hubCurrentCrumb];
  }

  const handleBack =
    onBack ??
    (() =>
      navigate(sourceDisplayName || crumbs ? "/app/data/hub" : "/app/data"));

  return (
    <Box
      sx={{
        mb: 4,
        minHeight: "24px",
        display: "flex",
        alignItems: "center",
        gap: 2,
      }}
    >
      <IconButton
        onClick={handleBack}
        size="small"
        sx={{
          color: "text.secondary",
          "&:hover": { color: "primary.main", backgroundColor: "action.hover" },
        }}
        aria-label="Go back"
      >
        <ArrowBackIcon fontSize="small" />
      </IconButton>
      <Breadcrumbs
        aria-label="breadcrumb"
        sx={{ minHeight: "24px", display: "flex", alignItems: "center" }}
      >
        {resolvedCrumbs.map((crumb, index) => {
          const isLast = index === resolvedCrumbs.length - 1;
          if (isLast || !crumb.onClick) {
            return (
              <Typography key={index} color="text.primary">
                {crumb.label}
              </Typography>
            );
          }
          return (
            <Link
              key={index}
              underline="hover"
              color="inherit"
              component="button"
              onClick={crumb.onClick}
              sx={{ cursor: "pointer" }}
            >
              {crumb.label}
            </Link>
          );
        })}
      </Breadcrumbs>
    </Box>
  );
}
