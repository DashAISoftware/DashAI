import { useState } from "react";
import PropTypes from "prop-types";
import { Virtuoso } from "react-virtuoso";
import {
  Box,
  Checkbox,
  CircularProgress,
  Link,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { getNotebookDocumentOutline } from "../../../api/notebook";
import { normalizeUrl } from "../../../utils/urlUtils";
import { kindColor, kindLabel } from "../../documents/documentKinds";
import useNotebookItems from "./useNotebookItems";

const ROW_HEIGHT = 44;
const LIST_HEIGHT = 264;

function PickerRow({ item, checked, onToggle }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  return (
    <Box
      component="label"
      sx={{
        display: "grid",
        gridTemplateColumns: "32px 40px 128px 1fr",
        alignItems: "center",
        columnGap: 1.5,
        minHeight: ROW_HEIGHT,
        px: 1,
        borderBottom: 1,
        borderColor: "divider",
        cursor: "pointer",
        bgcolor: checked ? theme.palette.action.selected : "transparent",
        "&:hover": { bgcolor: theme.palette.action.hover },
      }}
    >
      <Checkbox
        size="small"
        checked={checked}
        onChange={onToggle}
        sx={{ p: 0.5 }}
      />
      <Typography
        sx={{
          fontSize: "12px",
          color: "text.secondary",
          fontVariantNumeric: "tabular-nums",
          textAlign: "right",
        }}
      >
        {item.position + 1}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, minWidth: 0 }}>
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            bgcolor: kindColor(theme, item.kind),
            flexShrink: 0,
          }}
        />
        <Typography sx={{ fontSize: "13px" }} noWrap>
          {kindLabel(t, item.kind)}
        </Typography>
      </Box>
      {item.type === "Image" ? (
        <Box
          component="img"
          src={normalizeUrl(item.url)}
          alt={t("datasets:document.imageAlt", { position: item.position + 1 })}
          loading="lazy"
          sx={{
            display: "block",
            maxHeight: 32,
            maxWidth: 96,
            borderRadius: 0.5,
          }}
        />
      ) : (
        <Typography sx={{ fontSize: "13px", minWidth: 0 }} noWrap>
          {item.content}
        </Typography>
      )}
    </Box>
  );
}

PickerRow.propTypes = {
  item: PropTypes.shape({
    type: PropTypes.string,
    kind: PropTypes.string,
    position: PropTypes.number,
    content: PropTypes.string,
    url: PropTypes.string,
  }).isRequired,
  checked: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
};

export default function DocumentItemPicker({
  notebookId,
  typeName,
  kinds,
  picked,
  onToggleItem,
  onSelectAll,
  onClear,
}) {
  const { t } = useTranslation(["datasets"]);
  const content = useNotebookItems(notebookId, typeName, kinds, null);
  const [selecting, setSelecting] = useState(false);
  const pickedCount = Object.keys(picked).length;
  const allPicked = content.total > 0 && pickedCount >= content.total;

  const toggleAll = async () => {
    if (allPicked) {
      onClear();
      return;
    }
    setSelecting(true);
    try {
      const outline = await getNotebookDocumentOutline(notebookId);
      onSelectAll(
        Object.fromEntries(
          outline.items
            .filter(
              (item) => item.type === typeName && kinds.includes(item.kind),
            )
            .map((item) => [item.position, item.kind]),
        ),
      );
    } catch (error) {
      console.error("Failed to select every item:", error);
    } finally {
      setSelecting(false);
    }
  };

  return (
    <Box sx={{ mt: 1.5 }}>
      <Box sx={{ display: "flex", alignItems: "baseline", gap: 2, mb: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ flex: 1 }}>
          {pickedCount > 0
            ? t("datasets:documentNotebook.scopePicked", { count: pickedCount })
            : t("datasets:documentNotebook.scopePickHint")}
        </Typography>
        {pickedCount > 0 && (
          <Link
            component="button"
            type="button"
            variant="caption"
            onClick={onClear}
          >
            {t("datasets:documentNotebook.scopeClearPicked")}
          </Link>
        )}
      </Box>
      <Box
        sx={{
          border: 1,
          borderColor: "divider",
          borderRadius: 1,
          bgcolor: "background.paper",
          overflow: "hidden",
        }}
      >
        {content.items.length === 0 ? (
          <Box
            sx={{
              height: 88,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {content.loading ? (
              <CircularProgress size={20} />
            ) : (
              <Typography variant="body2" color="text.secondary">
                {t("datasets:documentNotebook.noItems")}
              </Typography>
            )}
          </Box>
        ) : (
          <>
            <Box
              component="label"
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.5,
                minHeight: ROW_HEIGHT,
                px: 1,
                borderBottom: 1,
                borderColor: "divider",
                cursor: selecting ? "progress" : "pointer",
              }}
            >
              <Checkbox
                size="small"
                checked={allPicked}
                indeterminate={pickedCount > 0 && !allPicked}
                disabled={selecting}
                onChange={toggleAll}
                sx={{ p: 0.5 }}
              />
              <Typography sx={{ fontSize: "13px", fontWeight: 600 }}>
                {t("datasets:documentNotebook.scopeSelectAllItems", {
                  count: content.total,
                })}
              </Typography>
              {selecting && <CircularProgress size={14} />}
            </Box>
            <Virtuoso
              style={{
                height: Math.min(
                  LIST_HEIGHT,
                  content.items.length * ROW_HEIGHT + 2,
                ),
              }}
              data={content.items}
              endReached={content.loadMore}
              computeItemKey={(index, item) => item.position}
              itemContent={(index, item) => (
                <PickerRow
                  item={item}
                  checked={item.position in picked}
                  onToggle={() => onToggleItem(item)}
                />
              )}
            />
          </>
        )}
      </Box>
    </Box>
  );
}

DocumentItemPicker.propTypes = {
  notebookId: PropTypes.number.isRequired,
  typeName: PropTypes.string.isRequired,
  kinds: PropTypes.arrayOf(PropTypes.string).isRequired,
  picked: PropTypes.objectOf(PropTypes.string).isRequired,
  onToggleItem: PropTypes.func.isRequired,
  onSelectAll: PropTypes.func.isRequired,
  onClear: PropTypes.func.isRequired,
};
