import PropTypes from "prop-types";
import { Box } from "@mui/material";
import { useTheme } from "@mui/material/styles";

export default function TagBadges({ tags, sx }) {
  const theme = useTheme();

  if (!tags || tags.length === 0) return null;

  return (
    <Box sx={{ display: "flex", gap: "5px", flexWrap: "wrap", ...sx }}>
      {tags.map((tag) => (
        <Box
          key={tag}
          sx={{
            ...theme.typography.statusBadge,
            border: `1px solid ${theme.palette.divider}`,
            color: theme.palette.text.secondary,
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
  );
}

TagBadges.propTypes = {
  tags: PropTypes.arrayOf(PropTypes.string),
  sx: PropTypes.object,
};
