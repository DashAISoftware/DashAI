import React from "react";
import { Box, Typography, ButtonBase, Tooltip, useTheme } from "@mui/material";
import PropTypes from "prop-types";
import { useNavigate, useParams } from "react-router-dom";
import usePluginsUpdate from "../hooks/usePluginsUpdate";
import { PluginStatus } from "../../../types/plugin";
import CircularProgress from "@mui/material/CircularProgress";
import { useTranslation } from "react-i18next";
import {
  Extension as PluginIcon,
  Verified as VerifiedIcon,
} from "@mui/icons-material";

const DESCRIPTION_MAX_LINES = 3;

function PluginsCard({
  plugin,
  cardView,
  refreshPluginsFlag,
  setRefreshPluginsFlag,
}) {
  const navigate = useNavigate();
  const { category } = useParams();
  const { t } = useTranslation(["plugins"]);
  const theme = useTheme();

  const accent = theme.palette.primary.main;
  const accentDim = `${accent}1F`;
  const accentBorder = `${accent}38`;
  const accentGlow = `${accent}0A`;

  const descRef = React.useRef(null);
  const [isTruncated, setIsTruncated] = React.useState(false);

  React.useEffect(() => {
    const el = descRef.current;
    if (el) {
      setIsTruncated(el.scrollHeight > el.clientHeight);
    }
  }, [plugin.summary, cardView]);

  const handlePluginClick = () => {
    navigate(`/app/plugins/${category}/details/${plugin.id}`);
  };

  const { updatePlugin, loading } = usePluginsUpdate({
    pluginId: plugin.id,
    newStatus: PluginStatus.INSTALLED,
    onSuccess: () => {
      setRefreshPluginsFlag(true);
    },
  });

  const displayName = plugin.name.replace("dashai-", "");
  const tags = plugin.tags.map((tag) => tag.name);

  const verifiedBadge = plugin.verified ? (
    <Tooltip title={t("plugins:label.verified")} arrow placement="top">
      <VerifiedIcon sx={{ fontSize: 16, color: accent, flexShrink: 0 }} />
    </Tooltip>
  ) : null;
  const version = plugin.installed_version
    ? `v${plugin.installed_version}`
    : null;

  if (!cardView) {
    return (
      <ButtonBase
        onClick={handlePluginClick}
        sx={{
          width: "100%",
          textAlign: "left",
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          background: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: "4px",
          padding: "14px 24px",
          cursor: "pointer",
          position: "relative",
          overflow: "hidden",
          transition: "border-color 0.2s, background 0.2s, transform 0.15s",
          gap: 12,
          "&:hover": {
            borderColor: accentBorder,
            background: accentGlow,
          },
        }}
      >
        <Box
          sx={{
            width: 34,
            height: 34,
            borderRadius: "6px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: accentDim,
            color: accent,
            flexShrink: 0,
          }}
        >
          <PluginIcon sx={{ fontSize: 20 }} />
        </Box>

        <Typography
          sx={{
            ...theme.typography.h5,
            color: theme.palette.text.primary,
            flexShrink: 0,
          }}
        >
          {displayName}
        </Typography>

        {verifiedBadge}

        {version && (
          <Typography
            variant="body1"
            sx={{
              fontWeight: 300,
              color: theme.palette.text.disabled,
              flexShrink: 0,
            }}
          >
            {version}
          </Typography>
        )}

        <Typography
          variant="body1"
          sx={{
            fontWeight: 300,
            color: theme.palette.text.secondary,
            flexGrow: 1,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {plugin.summary}
        </Typography>

        <Box sx={{ display: "flex", gap: "5px", flexShrink: 0 }}>
          {tags.map((tag) => (
            <Box
              key={tag}
              sx={{
                ...theme.typography.statusBadge,
                border: `1px solid ${theme.palette.divider}`,
                color: theme.palette.text.disabled,
                px: "7px",
                py: "2px",
                borderRadius: "2px",
                background: theme.palette.background.default,
              }}
            >
              {tag}
            </Box>
          ))}
        </Box>

        {plugin.status === PluginStatus.REGISTERED && (
          <Box
            component="span"
            onClick={(e) => {
              e.stopPropagation();
              updatePlugin();
            }}
            sx={{
              fontSize: "12px",
              fontWeight: 500,
              color: accent,
              cursor: "pointer",
              flexShrink: 0,
              "&:hover": { textDecoration: "underline" },
            }}
          >
            {loading ? (
              <CircularProgress size={16} />
            ) : (
              t("plugins:button.install")
            )}
          </Box>
        )}

        <Box
          className="card-arrow"
          sx={{
            fontSize: "18px",
            color: theme.palette.text.disabled,
            flexShrink: 0,
            ml: 8,
          }}
        >
          →
        </Box>
      </ButtonBase>
    );
  }

  return (
    <ButtonBase
      onClick={handlePluginClick}
      sx={{
        width: "100%",
        height: "100%",
        textAlign: "left",
        display: "flex",
        flexDirection: "column",
        background: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: "4px",
        padding: "22px 24px",
        cursor: "pointer",
        position: "relative",
        overflow: "hidden",
        transition: "border-color 0.2s, background 0.2s, transform 0.15s",
        "&::before": {
          content: '""',
          position: "absolute",
          top: 0,
          left: "10%",
          right: "10%",
          height: "1px",
          background: `linear-gradient(90deg, transparent, ${accent}, transparent)`,
          opacity: 0,
          transition: "opacity 0.25s",
        },
        "&:hover": {
          transform: "translateY(-1px)",
          borderColor: accentBorder,
          background: accentGlow,
        },
        "&:hover::before": {
          opacity: 1,
        },
        "&:hover .card-arrow": {
          transform: "translateX(3px)",
          color: accent,
        },
      }}
    >
      {/* Header: icon + version */}
      <Box
        sx={{
          display: "flex",
          mb: 3,
          width: "100%",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Box
          sx={{
            width: 38,
            height: 38,
            borderRadius: "6px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: accentDim,
            color: accent,
            flexShrink: 0,
          }}
        >
          <PluginIcon sx={{ fontSize: 25 }} />
        </Box>

        {version && (
          <Typography
            variant="body1"
            sx={{
              fontWeight: 300,
              color: theme.palette.text.disabled,
            }}
          >
            {version}
          </Typography>
        )}
      </Box>

      {/* Title */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          mb: 6,
          width: "100%",
        }}
      >
        <Typography
          noWrap
          sx={{
            ...theme.typography.h5,
            color: theme.palette.text.primary,
          }}
        >
          {displayName}
        </Typography>
        {verifiedBadge}
      </Box>

      {/* Description */}
      <Tooltip
        title={isTruncated ? plugin.summary : ""}
        arrow
        enterDelay={300}
        placement="bottom"
      >
        <Typography
          variant="subtitle2"
          ref={descRef}
          sx={{
            fontWeight: 300,
            color: theme.palette.text.secondary,
            lineHeight: 1.65,
            flexGrow: 1,
            width: "100%",
            display: "-webkit-box",
            WebkitLineClamp: DESCRIPTION_MAX_LINES,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {plugin.summary}
        </Typography>
      </Tooltip>

      {/* Footer: tags + install/arrow */}
      <Box
        sx={{
          mt: 4,
          pt: 3,
          borderTop: `1px solid ${theme.palette.ui.borderLight}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          width: "100%",
        }}
      >
        <Box sx={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
          {tags.map((tag) => (
            <Box
              key={tag}
              sx={{
                ...theme.typography.statusBadge,
                border: `1px solid ${theme.palette.divider}`,
                color: theme.palette.text.disabled,
                px: "7px",
                py: "2px",
                borderRadius: "2px",
                background: theme.palette.background.default,
              }}
            >
              {tag}
            </Box>
          ))}
        </Box>

        <Box sx={{ display: "flex", alignItems: "center", gap: 8 }}>
          {plugin.status === PluginStatus.REGISTERED && (
            <Box
              component="span"
              onClick={(e) => {
                e.stopPropagation();
                updatePlugin();
              }}
              sx={{
                fontSize: "12px",
                fontWeight: 500,
                color: accent,
                cursor: "pointer",
                "&:hover": { textDecoration: "underline" },
              }}
            >
              {loading ? (
                <CircularProgress size={16} />
              ) : (
                t("plugins:button.install")
              )}
            </Box>
          )}
          <Box
            className="card-arrow"
            sx={{
              fontSize: "18px",
              color: theme.palette.text.disabled,
              transition: "color 0.15s, transform 0.15s",
              flexShrink: 0,
            }}
          >
            →
          </Box>
        </Box>
      </Box>
    </ButtonBase>
  );
}

PluginsCard.propTypes = {
  plugin: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    author: PropTypes.string.isRequired,
    verified: PropTypes.bool,
    tags: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number.isRequired,
        name: PropTypes.string.isRequired,
        plugin_id: PropTypes.number.isRequired,
      }),
    ),
    status: PropTypes.oneOf([0, 1, 2, 3]).isRequired,
    summary: PropTypes.string.isRequired,
    description: PropTypes.string.isRequired,
    description_content_type: PropTypes.string.isRequired,
    created: PropTypes.string.isRequired,
    last_modified: PropTypes.string.isRequired,
  }).isRequired,
  cardView: PropTypes.bool.isRequired,
  refreshPluginsFlag: PropTypes.bool.isRequired,
  setRefreshPluginsFlag: PropTypes.func.isRequired,
};

export default PluginsCard;
