import { Box, Paper, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";

/**
 * Card displaying a single dataset from the Hub.
 *
 * @param {object} dataset - DatasetEntry object.
 * @param {boolean} selected - Whether this card is currently selected.
 * @param {function} onSelect - Called when the card is clicked.
 */
export default function DatasetCard({ dataset, selected, onSelect }) {
  const theme = useTheme();

  return (
    <Paper
      elevation={0}
      onClick={onSelect}
      sx={{
        p: 1.5,
        cursor: "pointer",
        border: 1,
        borderColor: selected ? "primary.main" : "divider",
        bgcolor: selected ? "action.selected" : "background.paper",
        transition: "border-color 0.15s, background 0.15s",
        "&:hover": { borderColor: "secondary.main" },
        display: "flex",
        flexDirection: "column",
        gap: 0.75,
        height: 200,
        overflow: "hidden",
        minWidth: 0,
      }}
    >
      <Typography
        variant="subtitle2"
        fontWeight={600}
        sx={{
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
          wordBreak: "break-word",
          overflowWrap: "break-word",
        }}
      >
        {dataset.name}
      </Typography>

      {dataset.description && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            display: "-webkit-box",
            WebkitLineClamp: 4,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            wordBreak: "break-word",
            overflowWrap: "break-word",
          }}
        >
          {dataset.description}
        </Typography>
      )}

      <Box sx={{ flexGrow: 1 }} />

      <Box sx={{ display: "flex", gap: "5px", flexWrap: "wrap" }}>
        {dataset.tags?.slice(0, 3).map((tag) => (
          <Box
            key={tag}
            title={tag}
            sx={{
              ...theme.typography.statusBadge,
              lineHeight: 1,
              border: `1px solid ${theme.palette.divider}`,
              color: theme.palette.text.primary,
              px: "7px",
              py: "2px",
              borderRadius: "2px",
              background: theme.palette.background.default,
              maxWidth: "100%",
              minWidth: 0,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {tag}
          </Box>
        ))}
      </Box>
    </Paper>
  );
}
