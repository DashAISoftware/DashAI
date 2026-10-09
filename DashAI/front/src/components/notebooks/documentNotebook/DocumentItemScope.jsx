import { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  ButtonBase,
  Checkbox,
  Link,
  Radio,
  Typography,
} from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { evaluateColumnEligibility } from "../../../utils/columnEligibility";
import {
  KIND_ORDER,
  kindColor,
  kindLabel,
} from "../../documents/documentKinds";
import { CONTENT_TYPE_ICONS, contentTypeLabel } from "./documentItems";
import DocumentItemPicker from "./DocumentItemPicker";

function sortedKinds(kinds) {
  const rank = (kind) => {
    const index = KIND_ORDER.indexOf(kind);
    return index === -1 ? KIND_ORDER.length : index;
  };
  return Object.keys(kinds || {}).sort((a, b) => rank(a) - rank(b));
}

function cardinalityHolds(cardinality, count) {
  if (cardinality.exact !== undefined && count !== cardinality.exact) {
    return false;
  }
  if (cardinality.min !== undefined && count < cardinality.min) return false;
  if (cardinality.max !== undefined && count > cardinality.max) return false;
  return count > 0;
}

function KindChip({ kind, count, selected, onToggle }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const color = kindColor(theme, kind);
  return (
    <ButtonBase
      onClick={onToggle}
      aria-pressed={selected}
      sx={{
        display: "inline-flex",
        alignItems: "center",
        gap: 1,
        px: 1.5,
        py: 0.5,
        borderRadius: 999,
        border: 1,
        borderColor: selected ? color : theme.palette.ui.border,
        bgcolor: selected ? alpha(color, 0.14) : "transparent",
        color: selected ? "text.primary" : "text.secondary",
        fontSize: "13px",
        transition: "background-color 0.15s, border-color 0.15s",
        "&:hover": { borderColor: color },
        "&.Mui-focusVisible": {
          outline: `2px solid ${theme.palette.primary.main}`,
          outlineOffset: "2px",
        },
      }}
    >
      <Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: color }} />
      {kindLabel(t, kind)}
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

KindChip.propTypes = {
  kind: PropTypes.string.isRequired,
  count: PropTypes.number.isRequired,
  selected: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
};

function TypeCard({
  notebookId,
  typeName,
  info,
  eligible,
  single,
  kinds,
  picked,
  pickerOpen,
  onToggleType,
  onToggleKind,
  onSetKinds,
  onTogglePicker,
  onToggleItem,
  onSelectAllItems,
  onClearPicked,
}) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const selected = kinds !== undefined;
  const Icon = CONTENT_TYPE_ICONS[typeName];
  const Control = single ? Radio : Checkbox;
  const allKinds = sortedKinds(info.kinds);
  return (
    <Box
      sx={{
        border: 1,
        borderColor: selected ? "primary.main" : theme.palette.ui.border,
        borderRadius: 1,
        opacity: eligible ? 1 : 0.55,
        bgcolor: selected
          ? alpha(theme.palette.primary.main, 0.04)
          : "transparent",
      }}
    >
      <Box
        component="label"
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          px: 2,
          py: 1.5,
          cursor: eligible ? "pointer" : "not-allowed",
        }}
      >
        <Control
          checked={selected}
          disabled={!eligible}
          onChange={onToggleType}
          size="small"
          sx={{ p: 0.5 }}
        />
        {Icon && <Icon sx={{ fontSize: 20, color: "text.secondary" }} />}
        <Typography sx={{ fontWeight: 600, flex: 1 }}>
          {contentTypeLabel(t, typeName)}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {eligible
            ? t("datasets:documentNotebook.itemCount", { count: info.count })
            : t("datasets:documentNotebook.scopeNotCompatible")}
        </Typography>
      </Box>
      {selected && (
        <Box sx={{ px: 2, pb: 2, pl: 7 }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "baseline",
              gap: 2,
              mb: 1,
            }}
          >
            <Typography variant="caption" color="text.secondary">
              {t("datasets:documentNotebook.scopeKinds")}
            </Typography>
            <Link
              component="button"
              type="button"
              variant="caption"
              onClick={() => onSetKinds(allKinds)}
            >
              {t("datasets:documentNotebook.selectAll")}
            </Link>
            <Link
              component="button"
              type="button"
              variant="caption"
              onClick={() => onSetKinds([])}
            >
              {t("datasets:documentNotebook.selectNone")}
            </Link>
          </Box>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {allKinds.map((kind) => (
              <KindChip
                key={kind}
                kind={kind}
                count={info.kinds[kind]}
                selected={kinds.includes(kind)}
                onToggle={() => onToggleKind(kind)}
              />
            ))}
          </Box>
          {kinds.length === 0 ? (
            <Typography
              variant="caption"
              color="error"
              sx={{ display: "block", mt: 1 }}
            >
              {t("datasets:documentNotebook.scopePickKind")}
            </Typography>
          ) : (
            <>
              <Link
                component="button"
                type="button"
                variant="caption"
                onClick={onTogglePicker}
                aria-expanded={pickerOpen}
                sx={{ display: "block", mt: 1.5 }}
              >
                {pickerOpen
                  ? t("datasets:documentNotebook.scopeHideItems")
                  : t("datasets:documentNotebook.scopePickItems")}
              </Link>
              {pickerOpen && (
                <DocumentItemPicker
                  notebookId={notebookId}
                  typeName={typeName}
                  kinds={kinds}
                  picked={picked}
                  onToggleItem={onToggleItem}
                  onSelectAll={onSelectAllItems}
                  onClear={onClearPicked}
                />
              )}
            </>
          )}
        </Box>
      )}
    </Box>
  );
}

TypeCard.propTypes = {
  notebookId: PropTypes.number.isRequired,
  typeName: PropTypes.string.isRequired,
  info: PropTypes.object.isRequired,
  eligible: PropTypes.bool.isRequired,
  single: PropTypes.bool.isRequired,
  kinds: PropTypes.arrayOf(PropTypes.string),
  picked: PropTypes.objectOf(PropTypes.string).isRequired,
  pickerOpen: PropTypes.bool.isRequired,
  onToggleType: PropTypes.func.isRequired,
  onToggleKind: PropTypes.func.isRequired,
  onSetKinds: PropTypes.func.isRequired,
  onTogglePicker: PropTypes.func.isRequired,
  onToggleItem: PropTypes.func.isRequired,
  onSelectAllItems: PropTypes.func.isRequired,
  onClearPicked: PropTypes.func.isRequired,
};

function keepPicked(picked, kinds) {
  return Object.fromEntries(
    Object.entries(picked || {}).filter(([, kind]) => kinds.includes(kind)),
  );
}

function initialState(columnTypes, eligibleTypes, initialSelection) {
  const preferred = initialSelection?.type;
  if (preferred && eligibleTypes.includes(preferred)) {
    const present = sortedKinds(columnTypes[preferred]?.kinds);
    const wanted = (initialSelection.kinds || []).filter((kind) =>
      present.includes(kind),
    );
    return { [preferred]: wanted.length > 0 ? wanted : present };
  }
  const first = eligibleTypes[0];
  if (!first) return {};
  return { [first]: sortedKinds(columnTypes[first].kinds) };
}

export default function DocumentItemScope({
  notebookId,
  columnTypes,
  metadata,
  single = false,
  initialSelection = null,
  onSelectionChange,
  onValidationChange,
}) {
  const { t } = useTranslation(["datasets", "common"]);
  const typeNames = useMemo(
    () => Object.keys(columnTypes || {}),
    [columnTypes],
  );
  const eligibleTypes = useMemo(
    () =>
      typeNames.filter((typeName) => {
        const column = {
          columnName: typeName,
          valueType: columnTypes[typeName].type,
          dataType: columnTypes[typeName].dtype,
        };
        const { validColumns } = evaluateColumnEligibility(
          { ...metadata, input_cardinality: {} },
          [column],
        );
        return validColumns.length === 1;
      }),
    [typeNames, columnTypes, metadata],
  );
  const [selection, setSelection] = useState(() =>
    initialState(columnTypes, eligibleTypes, initialSelection),
  );
  const [picked, setPicked] = useState({});
  const [openPickers, setOpenPickers] = useState([]);

  const selectedTypes = Object.keys(selection);
  const cardinality = single
    ? { exact: 1 }
    : metadata?.input_cardinality || { min: 1 };
  const isValid =
    cardinalityHolds(cardinality, selectedTypes.length) &&
    selectedTypes.every((typeName) => selection[typeName].length > 0);

  const total = typeNames.reduce(
    (sum, typeName) => sum + (columnTypes[typeName].count || 0),
    0,
  );
  const selectedCount = selectedTypes.reduce((sum, typeName) => {
    const pickedCount = Object.keys(picked[typeName] || {}).length;
    if (pickedCount > 0) return sum + pickedCount;
    return (
      sum +
      selection[typeName].reduce(
        (kindSum, kind) => kindSum + (columnTypes[typeName].kinds?.[kind] || 0),
        0,
      )
    );
  }, 0);

  useEffect(() => {
    const columns = selectedTypes.map((typeName, index) => {
      const present = sortedKinds(columnTypes[typeName].kinds);
      const kinds = selection[typeName];
      const everyKind = present.every((kind) => kinds.includes(kind));
      const positions = Object.keys(picked[typeName] || {})
        .map(Number)
        .sort((a, b) => a - b);
      return {
        id: index,
        columnName: typeName,
        valueType: columnTypes[typeName].type,
        dataType: columnTypes[typeName].dtype,
        ...(everyKind ? {} : { kinds }),
        ...(positions.length > 0 ? { positions } : {}),
      };
    });
    onSelectionChange(columns);
    onValidationChange(isValid);
  }, [selection, picked, columnTypes, isValid]);

  const updatePicked = (typeName, update) => {
    setPicked((current) => ({
      ...current,
      [typeName]: update(current[typeName] || {}),
    }));
  };

  const toggleType = (typeName) => {
    if (!single && selection[typeName] !== undefined) {
      updatePicked(typeName, () => ({}));
    }
    setSelection((current) => {
      if (current[typeName] !== undefined) {
        if (single) return current;
        return Object.fromEntries(
          Object.entries(current).filter(([name]) => name !== typeName),
        );
      }
      const kinds = sortedKinds(columnTypes[typeName].kinds);
      return single ? { [typeName]: kinds } : { ...current, [typeName]: kinds };
    });
  };

  const toggleKind = (typeName, kind) => {
    const kinds = selection[typeName] || [];
    const next = kinds.includes(kind)
      ? kinds.filter((value) => value !== kind)
      : [...kinds, kind];
    updatePicked(typeName, (current) => keepPicked(current, next));
    setSelection((current) => ({ ...current, [typeName]: next }));
  };

  const setKinds = (typeName, kinds) => {
    updatePicked(typeName, (current) => keepPicked(current, kinds));
    setSelection((current) => ({ ...current, [typeName]: kinds }));
  };

  const togglePicker = (typeName) => {
    setOpenPickers((current) =>
      current.includes(typeName)
        ? current.filter((name) => name !== typeName)
        : [...current, typeName],
    );
  };

  const toggleItem = (typeName, item) => {
    updatePicked(typeName, (current) => {
      if (item.position in current) {
        return Object.fromEntries(
          Object.entries(current).filter(
            ([position]) => Number(position) !== item.position,
          ),
        );
      }
      return { ...current, [item.position]: item.kind };
    });
  };

  if (typeNames.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        {t("datasets:documentNotebook.noItems")}
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {typeNames.map((typeName) => (
        <TypeCard
          key={typeName}
          notebookId={notebookId}
          typeName={typeName}
          info={columnTypes[typeName]}
          eligible={eligibleTypes.includes(typeName)}
          single={single}
          kinds={selection[typeName]}
          picked={picked[typeName] || {}}
          pickerOpen={openPickers.includes(typeName)}
          onToggleType={() => toggleType(typeName)}
          onToggleKind={(kind) => toggleKind(typeName, kind)}
          onSetKinds={(kinds) => setKinds(typeName, kinds)}
          onTogglePicker={() => togglePicker(typeName)}
          onToggleItem={(item) => toggleItem(typeName, item)}
          onSelectAllItems={(entries) => updatePicked(typeName, () => entries)}
          onClearPicked={() => updatePicked(typeName, () => ({}))}
        />
      ))}
      <Typography variant="body2" color="text.secondary">
        {t("datasets:documentNotebook.scopeSummary", {
          selected: selectedCount,
          total,
        })}
      </Typography>
    </Box>
  );
}

DocumentItemScope.propTypes = {
  notebookId: PropTypes.number.isRequired,
  columnTypes: PropTypes.object.isRequired,
  metadata: PropTypes.object,
  single: PropTypes.bool,
  initialSelection: PropTypes.shape({
    type: PropTypes.string,
    kinds: PropTypes.arrayOf(PropTypes.string),
  }),
  onSelectionChange: PropTypes.func.isRequired,
  onValidationChange: PropTypes.func.isRequired,
};
