import PropTypes from "prop-types";
import { Box, Button, Chip, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { kindColor, kindLabel, orderedKinds } from "./documentKinds";

export default function DocumentKindFilter({
  counts,
  selected,
  onChange,
  shown,
}) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const kinds = orderedKinds(counts);
  const matching = kinds
    .filter((kind) => selected.includes(kind))
    .reduce((sum, kind) => sum + counts[kind], 0);

  const toggle = (kind) =>
    onChange(
      selected.includes(kind)
        ? selected.filter((value) => value !== kind)
        : [...selected, kind],
    );

  return (
    <Box sx={{ mb: 2 }}>
      <Box
        role="group"
        aria-label={t("datasets:document.filterByKind")}
        sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}
      >
        {kinds.map((kind) => {
          const isSelected = selected.includes(kind);
          const color = kindColor(theme, kind);
          return (
            <Chip
              key={kind}
              size="small"
              clickable
              aria-pressed={isSelected}
              onClick={() => toggle(kind)}
              variant={isSelected ? "filled" : "outlined"}
              icon={
                <Box
                  component="span"
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: "50%",
                    bgcolor: color,
                    flexShrink: 0,
                  }}
                />
              }
              label={`${kindLabel(t, kind)} ${counts[kind]}`}
              sx={{
                fontVariantNumeric: "tabular-nums",
                borderColor: isSelected ? color : "divider",
                "& .MuiChip-icon": { ml: 1, mr: -0.25 },
              }}
            />
          );
        })}
      </Box>
      {selected.length > 0 && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 1 }}>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontVariantNumeric: "tabular-nums" }}
          >
            {t("datasets:document.filterShown", { shown, total: matching })}
          </Typography>
          <Button size="small" onClick={() => onChange([])}>
            {t("datasets:document.clearFilter")}
          </Button>
        </Box>
      )}
    </Box>
  );
}

DocumentKindFilter.propTypes = {
  counts: PropTypes.objectOf(PropTypes.number).isRequired,
  selected: PropTypes.arrayOf(PropTypes.string).isRequired,
  onChange: PropTypes.func.isRequired,
  shown: PropTypes.number.isRequired,
};
