import { useMemo, useState } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { Box, ButtonBase, Chip, Tooltip, Typography } from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import RadioButtonCheckedIcon from "@mui/icons-material/RadioButtonChecked";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import SearchBar from "../../threeSectionLayout/SearchBar";

const SEARCH_THRESHOLD = 5;
const VISIBLE_EXTENSIONS = 3;
const LIST_MAX_HEIGHT = 264;

function loaderLabel(loader) {
  return loader.display_name || loader.name;
}

function loaderExtensions(loader) {
  return loader.metadata?.supported_extensions ?? [];
}

function matchesQuery(loader, needle) {
  if (!needle) return true;
  return [
    loader.name,
    loader.display_name,
    loader.description,
    ...loaderExtensions(loader),
  ]
    .filter((value) => typeof value === "string")
    .some((value) => value.toLowerCase().includes(needle));
}

function ExtensionChip({ label, tooltip }) {
  const chip = (
    <Chip
      label={label}
      size="small"
      variant="outlined"
      sx={{ height: 20, "& .MuiChip-label": { px: 0.75, fontSize: 11 } }}
    />
  );
  return tooltip ? <Tooltip title={tooltip}>{chip}</Tooltip> : chip;
}

function ParserRow({ loader, selected, disabled, onSelect }) {
  const theme = useTheme();
  const accent = theme.palette.primary.main;
  const extensions = loaderExtensions(loader);
  const shown = extensions.slice(0, VISIBLE_EXTENSIONS);
  const hidden = extensions.slice(VISIBLE_EXTENSIONS);
  const RadioIcon = selected
    ? RadioButtonCheckedIcon
    : RadioButtonUncheckedIcon;

  return (
    <ButtonBase
      role="radio"
      aria-checked={selected}
      disabled={disabled}
      onClick={onSelect}
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1.5,
        width: "100%",
        px: 1.5,
        py: 1,
        minHeight: 44,
        textAlign: "left",
        justifyContent: "flex-start",
        borderBottom: 1,
        borderColor: "divider",
        "&:last-of-type": { borderBottom: 0 },
        bgcolor: selected ? alpha(accent, 0.08) : "transparent",
        opacity: disabled ? 0.45 : 1,
        transition: "background-color 0.15s",
        "&:hover": {
          bgcolor: selected ? alpha(accent, 0.12) : "action.hover",
        },
        "&.Mui-focusVisible": {
          outline: `2px solid ${accent}`,
          outlineOffset: "-2px",
        },
      }}
    >
      <RadioIcon
        sx={{
          fontSize: 18,
          color: selected ? "primary.main" : "text.disabled",
          flexShrink: 0,
        }}
      />
      <Typography
        variant="body2"
        noWrap
        sx={{ flex: 1, minWidth: 0, fontWeight: selected ? 600 : 400 }}
      >
        {loaderLabel(loader)}
      </Typography>
      {extensions.length > 0 && (
        <Box sx={{ display: "flex", gap: 0.5, flexShrink: 0 }}>
          {shown.map((extension) => (
            <ExtensionChip key={extension} label={extension} />
          ))}
          {hidden.length > 0 && (
            <ExtensionChip
              label={`+${hidden.length}`}
              tooltip={hidden.join(", ")}
            />
          )}
        </Box>
      )}
    </ButtonBase>
  );
}

export default function ParserSelector({
  loaders,
  isCompatible,
  selectedName,
  onSelect,
}) {
  const { t } = useTranslation(["generative"]);
  const [query, setQuery] = useState("");

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return loaders
      .filter((loader) => matchesQuery(loader, needle))
      .map((loader) => ({ loader, compatible: isCompatible(loader) }))
      .sort(
        (a, b) =>
          Number(b.compatible) - Number(a.compatible) ||
          loaderLabel(a.loader).localeCompare(loaderLabel(b.loader)),
      );
  }, [loaders, query, isCompatible]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
      <Typography
        variant="overline"
        color="text.secondary"
        sx={{ display: "block", lineHeight: 2 }}
      >
        {t("generative:documentsBar.parserLabel")}
      </Typography>
      {loaders.length > SEARCH_THRESHOLD && (
        <SearchBar
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("generative:documentsBar.searchParsers")}
        />
      )}
      <Box
        role="radiogroup"
        aria-label={t("generative:documentsBar.parserLabel")}
        sx={{
          border: 1,
          borderColor: "divider",
          borderRadius: 1,
          maxHeight: LIST_MAX_HEIGHT,
          overflowY: "auto",
        }}
      >
        {visible.length === 0 ? (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ p: 2, textAlign: "center" }}
          >
            {t("generative:documentsBar.noParsersFound")}
          </Typography>
        ) : (
          visible.map(({ loader, compatible }) => (
            <ParserRow
              key={loader.name}
              loader={loader}
              selected={selectedName === loader.name}
              disabled={!compatible}
              onSelect={() => onSelect(loader.name)}
            />
          ))
        )}
      </Box>
    </Box>
  );
}

ExtensionChip.propTypes = {
  label: PropTypes.string.isRequired,
  tooltip: PropTypes.string,
};

ParserRow.propTypes = {
  loader: PropTypes.object.isRequired,
  selected: PropTypes.bool.isRequired,
  disabled: PropTypes.bool.isRequired,
  onSelect: PropTypes.func.isRequired,
};

ParserSelector.propTypes = {
  loaders: PropTypes.arrayOf(PropTypes.object).isRequired,
  isCompatible: PropTypes.func.isRequired,
  selectedName: PropTypes.string,
  onSelect: PropTypes.func.isRequired,
};
