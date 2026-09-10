import React from "react";
import PropTypes from "prop-types";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { Link as RouterLink } from "react-router-dom";
import { useTheme } from "@mui/material/styles";

function HomeButton({
  title,
  description,
  to,
  Icon,
  accent,
  accentDim,
  accentBorder,
  accentGlow,
  tag,
  chips,
}) {
  const theme = useTheme();

  return (
    <Box
      component={RouterLink}
      to={to}
      sx={{
        display: "flex",
        flexDirection: "column",
        height: { xs: "auto", lg: "100%" },
        minHeight: { xs: 200, lg: 0 },
        background: theme.palette.background.paper,
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: "4px",
        padding: "22px 24px",
        textDecoration: "none",
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
      {/* Header: icon + tag */}
      <Box
        sx={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          mb: "14px",
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
          <Icon sx={{ fontSize: 25 }} />
        </Box>
        <Box sx={{ textAlign: "right", display: { xs: "none", lg: "block" } }}>
          <Box
            sx={{
              ...theme.typography.statusBadge,
              px: "8px",
              py: "3px",
              borderRadius: "2px",
              border: `1px solid ${accentBorder}`,
              background: accentDim,
              color: accent,
              display: "inline-block",
            }}
          >
            {tag}
          </Box>
        </Box>
      </Box>

      {/* Title */}
      <Typography
        variant="h4"
        sx={{
          color: theme.palette.text.primary,
          mb: "5px",
        }}
      >
        {title}
      </Typography>

      {/* Description */}
      <Typography
        variant="body1"
        sx={{
          fontWeight: 300,
          color: theme.palette.text.secondary,
          lineHeight: 1.65,
          flexGrow: 1,
        }}
      >
        {description}
      </Typography>

      {/* Footer: chips + arrow */}
      <Box
        sx={{
          mt: "16px",
          pt: "14px",
          borderTop: `1px solid ${theme.palette.ui.borderLight}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Box
          sx={{
            display: { xs: "none", lg: "flex" },
            gap: "5px",
            flexWrap: "wrap",
          }}
        >
          {chips.map((chip) => (
            <Box
              key={chip}
              sx={{
                ...theme.typography.statusBadge,
                border: `1px solid ${accentBorder}`,
                color: accent,
                px: "7px",
                py: "2px",
                borderRadius: "2px",
                background: accentDim,
              }}
            >
              {chip}
            </Box>
          ))}
        </Box>
        <Box
          className="card-arrow"
          sx={{
            fontSize: "22px",
            color: theme.palette.text.disabled,
            transition: "color 0.15s, transform 0.15s",
            flexShrink: 0,
            ml: 2,
          }}
        >
          →
        </Box>
      </Box>
    </Box>
  );
}

HomeButton.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  to: PropTypes.string.isRequired,
  Icon: PropTypes.elementType.isRequired,
  accent: PropTypes.string.isRequired,
  accentDim: PropTypes.string.isRequired,
  accentBorder: PropTypes.string.isRequired,
  accentGlow: PropTypes.string.isRequired,
  tag: PropTypes.string.isRequired,
  chips: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default HomeButton;
