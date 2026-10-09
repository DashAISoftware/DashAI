import { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { Virtuoso } from "react-virtuoso";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  ButtonBase,
  CircularProgress,
  Link,
  Typography,
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useTranslation } from "react-i18next";
import { normalizeUrl } from "../../../utils/urlUtils";
import {
  HIDDEN_KINDS,
  KIND_ORDER,
  kindColor,
  kindLabel,
} from "../../documents/documentKinds";
import { CONTENT_TYPE_ICONS, contentTypeLabel } from "./documentItems";
import useNotebookItems from "./useNotebookItems";

const LIST_HEIGHT = 420;

function orderedKinds(kinds) {
  const rank = (kind) => {
    const index = KIND_ORDER.indexOf(kind);
    return index === -1 ? KIND_ORDER.length : index;
  };
  return Object.keys(kinds || {}).sort((a, b) => rank(a) - rank(b));
}

function FilterPill({ label, count, selected, color, onClick }) {
  const theme = useTheme();
  const accent = color || theme.palette.primary.main;
  return (
    <ButtonBase
      onClick={onClick}
      aria-pressed={selected}
      sx={{
        display: "inline-flex",
        alignItems: "center",
        gap: 1,
        px: 1.5,
        py: 0.5,
        borderRadius: 999,
        border: 1,
        borderColor: selected ? accent : theme.palette.ui.border,
        bgcolor: selected ? alpha(accent, 0.14) : "transparent",
        color: selected ? "text.primary" : "text.secondary",
        fontSize: "13px",
        "&:hover": { borderColor: accent },
        "&.Mui-focusVisible": {
          outline: `2px solid ${theme.palette.primary.main}`,
          outlineOffset: "2px",
        },
      }}
    >
      {color && (
        <Box
          sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: color }}
        />
      )}
      {label}
      <Typography
        component="span"
        sx={{
          fontSize: "12px",
          color: "text.secondary",
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {count}
      </Typography>
    </ButtonBase>
  );
}

FilterPill.propTypes = {
  label: PropTypes.string.isRequired,
  count: PropTypes.number,
  selected: PropTypes.bool.isRequired,
  color: PropTypes.string,
  onClick: PropTypes.func.isRequired,
};

function ItemRow({ item, expanded, onToggle }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const color = kindColor(theme, item.kind);
  const isImage = item.type === "Image";
  const Icon = CONTENT_TYPE_ICONS[item.type];
  return (
    <ButtonBase
      component="div"
      onClick={onToggle}
      aria-expanded={expanded}
      sx={{
        display: "grid",
        gridTemplateColumns: "48px 56px 152px 1fr",
        columnGap: 2,
        alignItems: "start",
        width: "100%",
        textAlign: "left",
        px: 2,
        py: 1.25,
        borderBottom: 1,
        borderColor: "divider",
        "&:hover": { bgcolor: theme.palette.action.hover },
      }}
    >
      <Typography
        sx={{
          fontSize: "13px",
          color: "text.secondary",
          fontVariantNumeric: "tabular-nums",
          textAlign: "right",
          pt: "2px",
        }}
      >
        {item.position + 1}
      </Typography>
      <Typography
        sx={{
          fontSize: "13px",
          color: "text.secondary",
          fontVariantNumeric: "tabular-nums",
          pt: "2px",
        }}
      >
        {item.page ?? "-"}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, minWidth: 0 }}>
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            bgcolor: color,
            flexShrink: 0,
          }}
        />
        <Typography sx={{ fontSize: "13px", fontWeight: 600 }} noWrap>
          {kindLabel(t, item.kind)}
          {item.kind === "heading" && item.attrs?.level
            ? ` ${item.attrs.level}`
            : ""}
        </Typography>
        {Icon && (
          <Icon sx={{ fontSize: 15, color: "text.disabled", flexShrink: 0 }} />
        )}
      </Box>
      <Box sx={{ minWidth: 0 }}>
        {isImage ? (
          <Box
            component="img"
            src={normalizeUrl(item.url)}
            alt={
              item.attrs?.alt ||
              t("datasets:document.imageAlt", { position: item.position + 1 })
            }
            loading="lazy"
            sx={{
              display: "block",
              maxWidth: "100%",
              maxHeight: expanded ? 360 : 72,
              borderRadius: 1,
            }}
          />
        ) : (
          <Typography
            sx={{
              fontSize: "14px",
              lineHeight: 1.55,
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
              color: HIDDEN_KINDS.has(item.kind)
                ? "text.secondary"
                : "text.primary",
              ...(expanded
                ? {}
                : {
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }),
            }}
          >
            {item.content}
          </Typography>
        )}
      </Box>
    </ButtonBase>
  );
}

ItemRow.propTypes = {
  item: PropTypes.shape({
    type: PropTypes.string,
    kind: PropTypes.string,
    attrs: PropTypes.object,
    position: PropTypes.number,
    page: PropTypes.number,
    content: PropTypes.string,
    url: PropTypes.string,
  }).isRequired,
  expanded: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
};

export default function DocumentItemsPanel({
  notebookId,
  columnTypes,
  version,
  onFilterChange,
}) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const [contentType, setContentType] = useState("all");
  const [kinds, setKinds] = useState([]);
  const [expanded, setExpanded] = useState(() => new Set());
  const typeNames = Object.keys(columnTypes || {});
  const totalItems = typeNames.reduce(
    (sum, typeName) => sum + (columnTypes[typeName].count || 0),
    0,
  );

  const kindCounts = useMemo(() => {
    const counts = {};
    typeNames
      .filter((typeName) => contentType === "all" || typeName === contentType)
      .forEach((typeName) => {
        Object.entries(columnTypes[typeName].kinds || {}).forEach(
          ([kind, count]) => {
            counts[kind] = (counts[kind] || 0) + count;
          },
        );
      });
    return counts;
  }, [columnTypes, contentType, typeNames.join("|")]);

  useEffect(() => {
    if (contentType !== "all" && !typeNames.includes(contentType)) {
      setContentType("all");
    }
    setKinds((current) => current.filter((kind) => kind in kindCounts));
  }, [kindCounts, contentType, typeNames.join("|")]);

  useEffect(() => {
    onFilterChange(
      contentType === "all"
        ? null
        : { type: contentType, kinds: kinds.length > 0 ? kinds : null },
    );
  }, [contentType, kinds, onFilterChange]);

  const content = useNotebookItems(notebookId, contentType, kinds, version);

  const selectType = (typeName) => {
    setContentType(typeName);
    setKinds([]);
    setExpanded(new Set());
  };

  const toggleKind = (kind) => {
    setKinds((current) =>
      current.includes(kind)
        ? current.filter((value) => value !== kind)
        : [...current, kind],
    );
    setExpanded(new Set());
  };

  const toggleExpanded = (position) => {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(position)) next.delete(position);
      else next.add(position);
      return next;
    });
  };

  const filtered = contentType !== "all" || kinds.length > 0;

  return (
    <Accordion
      defaultExpanded
      disableGutters
      sx={{
        bgcolor: theme.palette.ui.box,
        borderRadius: 2,
        boxShadow: "none",
        "&::before": { display: "none" },
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon sx={{ color: "text.secondary" }} />}
        sx={{
          "& .MuiAccordionSummary-content": {
            alignItems: "baseline",
            gap: 2,
            my: 1.5,
          },
        }}
      >
        <Typography variant="h6">
          {t("datasets:documentNotebook.items")}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {filtered
            ? t("datasets:documentNotebook.itemsShown", {
                shown: content.total,
                total: totalItems,
              })
            : t("datasets:documentNotebook.itemCount", { count: totalItems })}
        </Typography>
      </AccordionSummary>

      <AccordionDetails sx={{ pt: 0 }}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5, mb: 2 }}>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            <FilterPill
              label={t("datasets:documentNotebook.allTypes")}
              count={totalItems}
              selected={contentType === "all"}
              onClick={() => selectType("all")}
            />
            {typeNames.map((typeName) => (
              <FilterPill
                key={typeName}
                label={contentTypeLabel(t, typeName)}
                count={columnTypes[typeName].count}
                selected={contentType === typeName}
                onClick={() => selectType(typeName)}
              />
            ))}
          </Box>
          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              gap: 1,
            }}
          >
            {orderedKinds(kindCounts).map((kind) => (
              <FilterPill
                key={kind}
                label={kindLabel(t, kind)}
                count={kindCounts[kind]}
                color={kindColor(theme, kind)}
                selected={kinds.includes(kind)}
                onClick={() => toggleKind(kind)}
              />
            ))}
            {filtered && (
              <Link
                component="button"
                type="button"
                variant="body2"
                onClick={() => selectType("all")}
                sx={{ ml: 1 }}
              >
                {t("datasets:documentNotebook.clearFilter")}
              </Link>
            )}
          </Box>
          <Typography variant="caption" color="text.secondary">
            {contentType === "all"
              ? t("datasets:documentNotebook.filterHint")
              : t("datasets:documentNotebook.filterSeedsTools")}
          </Typography>
        </Box>

        {content.failed && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {t("datasets:document.loadingFailed")}
          </Alert>
        )}

        <Box
          sx={{
            border: 1,
            borderColor: "divider",
            borderRadius: 1,
            bgcolor: "background.paper",
            overflow: "hidden",
          }}
        >
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "48px 56px 152px 1fr",
              columnGap: 2,
              px: 2,
              py: 1,
              borderBottom: 1,
              borderColor: "divider",
            }}
          >
            {[
              t("datasets:documentNotebook.columnPosition"),
              t("datasets:documentNotebook.columnPage"),
              t("datasets:documentNotebook.columnKind"),
              t("datasets:documentNotebook.columnContent"),
            ].map((label, index) => (
              <Typography
                key={label}
                variant="caption"
                color="text.secondary"
                sx={{
                  fontWeight: 600,
                  textAlign: index === 0 ? "right" : "left",
                }}
              >
                {label}
              </Typography>
            ))}
          </Box>
          {content.items.length === 0 ? (
            <Box
              sx={{
                height: 120,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {content.loading ? (
                <CircularProgress size={24} />
              ) : (
                <Typography variant="body2" color="text.secondary">
                  {t("datasets:documentNotebook.noItems")}
                </Typography>
              )}
            </Box>
          ) : (
            <Virtuoso
              style={{
                height: Math.min(LIST_HEIGHT, content.items.length * 64 + 8),
              }}
              data={content.items}
              endReached={content.loadMore}
              computeItemKey={(index, item) => item.position}
              itemContent={(index, item) => (
                <ItemRow
                  item={item}
                  expanded={expanded.has(item.position)}
                  onToggle={() => toggleExpanded(item.position)}
                />
              )}
              components={{
                Footer: () =>
                  content.loading ? (
                    <Box
                      sx={{ display: "flex", justifyContent: "center", py: 1 }}
                    >
                      <CircularProgress size={20} />
                    </Box>
                  ) : null,
              }}
            />
          )}
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}

DocumentItemsPanel.propTypes = {
  notebookId: PropTypes.number.isRequired,
  columnTypes: PropTypes.object.isRequired,
  version: PropTypes.any,
  onFilterChange: PropTypes.func.isRequired,
};
