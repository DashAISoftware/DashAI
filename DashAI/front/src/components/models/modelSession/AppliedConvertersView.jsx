import { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { Box, Chip, IconButton, Paper, Typography } from "@mui/material";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import DeleteIcon from "@mui/icons-material/Delete";
import Transform from "@mui/icons-material/Transform";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import DeleteConfirmationModal from "../../threeSectionLayout/DeleteConfirmationModal";
import ItemsToDeleteList from "../../notebooks/converter/ItemsToDeleteList";
import { useTableLocalization } from "../../../utils/useTableLocalization";
import { getColorByColumnType } from "../../../utils";
import { getComponentById, getComponents } from "../../../api/component";
import { getConvertersOutputSlots } from "../../../api/modelSession";

/**
 * Resolves one `input_scope` atom (the session converter's persisted scope
 * shape — `{kind: "column", name}` or `{kind: "group", converter_id, slot}`,
 * see `buildAtomList.js`) into a human-readable label, same
 * "ConverterName: slot label" convention `SessionInfoContent.jsx`'s
 * `formatColumnAtom` already uses for input/output columns. `converters`
 * is `session.converters` (to resolve a group atom's `converter_id` back
 * to the converter that produced it) and `converterTools` is the fetched
 * `Converter` component list (for that converter's translated
 * `display_name` and its declared `metadata.output_slots` labels) — never
 * falls back to a raw internal id/key, only to `t("common:unknown")` or
 * the atom's own `slot`/`name`.
 */
function formatScopeAtom(atom, converters, converterTools, t) {
  if (!atom) return t("common:unknown");
  if (atom.kind === "column") return atom.name;
  if (atom.kind === "group") {
    const sourceConverter = (converters || []).find(
      (c) => c.id === atom.converter_id,
    );
    if (!sourceConverter) return t("common:unknown");
    const toolDefinition = (converterTools || []).find(
      (tool) => tool.name === sourceConverter.converter,
    );
    const converterLabel =
      toolDefinition?.display_name || sourceConverter.converter;
    const slotDefinition = (toolDefinition?.metadata?.output_slots || []).find(
      (slot) => slot.slot === atom.slot,
    );
    return `${converterLabel}: ${slotDefinition?.label ?? atom.slot}`;
  }
  return t("common:unknown");
}

/**
 * The columns this converter's output group(s) will resolve to once the
 * session finalizes — the same "label + type chip" the wizard's Columns
 * step shows for a group atom (see ColumnsStep.jsx/DivideDatasetColumns.jsx),
 * shown here too so a converter's produced columns are visible right where
 * it's configured, not only two steps later. `outputSlots` is this specific
 * instance's real slots (fetched with its own `params`, not a generic
 * default-params lookup — see `getConvertersOutputSlots`), since some
 * converters (e.g. `SimpleImputer` with `add_indicator: true`) only declare
 * a second slot depending on their own configured parameters. Rendered as
 * one "Salida" row's value in `SessionConverterParametersTable`, alongside
 * "Columna Objetivo"/"Alcance - Columnas" — not a separate section — so
 * everything about this converter reads from a single table.
 */
function ConverterOutputChips({ converterLabel, outputSlots, theme }) {
  if (!outputSlots || outputSlots.length === 0) return "";

  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
      {outputSlots.map((slot) => {
        const typeColor = slot.type
          ? getColorByColumnType(slot.type, theme)
          : null;
        return (
          <Chip
            key={slot.slot}
            label={
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <span>
                  {converterLabel}: {slot.label}
                </span>
                {slot.type && (
                  <Chip
                    label={slot.type}
                    size="small"
                    sx={{
                      backgroundColor: typeColor,
                      color: "#fff",
                      fontWeight: 600,
                      fontSize: "0.65rem",
                      height: "16px",
                    }}
                  />
                )}
              </Box>
            }
          />
        );
      })}
    </Box>
  );
}

/**
 * Mirrors the notebook's own ConverterParametersTable (same columns, same
 * MaterialReactTable setup), sourced from the session converter's own
 * shape (`input_scope`/`target_column`) instead of the notebook's
 * (`parameters.scope.columns`/`parameters.scope.rows`/`parameters.target`).
 * No "Alcance - Filas" row: session converters have no row-level scope
 * (see ScopeStepSessionConverter.jsx). `scopeLabel` is precomputed by the
 * caller (`SessionConverterCard`), which has access to the full
 * `session.converters`/`converterTools` lookups a "group" atom needs to
 * resolve to a readable label. A "Salida" row (see `ConverterOutputChips`)
 * shows what this converter instance actually produces, right alongside
 * its other parameters.
 */
function SessionConverterParametersTable({
  converter,
  scopeLabel,
  converterLabel,
  outputSlots,
  t,
  theme,
  localization,
}) {
  const paramColumns = [
    { accessorKey: "key", header: t("common:parameter"), grow: 1 },
    { accessorKey: "value", header: t("common:value"), grow: 4 },
  ];

  const paramRows = [
    {
      key: t("datasets:label.targetColumn"),
      value: converter.target_column || "",
    },
    {
      key: t("datasets:label.scopeColumns"),
      value: scopeLabel,
    },
    {
      key: t("datasets:label.converterOutput"),
      value: (
        <ConverterOutputChips
          converterLabel={converterLabel}
          outputSlots={outputSlots}
          theme={theme}
        />
      ),
    },
  ];

  const table = useMaterialReactTable({
    columns: paramColumns,
    data: paramRows,
    muiTableBodyCellProps: { sx: { whiteSpace: "pre" } },
    localization,
    initialState: { density: "compact" },
    enablePagination: false,
    enableTopToolbar: false,
    enableBottomToolbar: false,
    enableColumnActions: false,
    enableSorting: false,
    enableColumnFilter: false,
    muiTablePaperProps: { elevation: 0 },
  });

  return <MaterialReactTable table={table} />;
}

/**
 * A single applied-converter card. Styled after the notebook's own
 * ConverterBox (icon + real component display name + description +
 * parameters table) but built against the session's converter shape
 * (`{id, converter, params, input_scope, target_column}`) instead of the
 * notebook's (`{parameters: {scope: {columns, rows}, target}}`) — reusing
 * ConverterBox directly left empty sections since those fields don't exist
 * here. No status dot: converters are no longer applied immediately when
 * added (see the module doc below), so there's no per-item async status to
 * show — every card would show the same "finished" dot regardless of
 * anything the user did, which is not a status, just noise. `scopeLabel`
 * is the already-formatted `input_scope` display string (see
 * `formatScopeAtom`), computed by the parent since resolving a "group" atom
 * needs the full sibling converter list/tool metadata, not just this one
 * card's own converter. `outputSlots` is this converter's real declared
 * output slots (see `ConverterOutputChips`).
 */
function SessionConverterCard({
  converter,
  scopeLabel,
  outputSlots,
  onDelete,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["common", "datasets"]);
  const localization = useTableLocalization();
  const [component, setComponent] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getComponentById(converter.converter)
      .then((data) => {
        if (!cancelled) setComponent(data);
      })
      .catch((error) => {
        console.error("Failed to fetch converter component:", error);
      });
    return () => {
      cancelled = true;
    };
  }, [converter.converter]);

  const converterLabel = component?.display_name || converter.converter;

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 4,
        bgcolor: "background.paper",
        borderColor: theme.palette.ui.border,
        borderRadius: 1,
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Transform sx={{ color: theme.palette.primary.main, fontSize: 20 }} />
          <Typography variant="subtitle2">{converterLabel}</Typography>
        </Box>
        <IconButton
          size="small"
          color="error"
          onClick={onDelete}
          aria-label={t("common:remove")}
        >
          <DeleteIcon fontSize="small" />
        </IconButton>
      </Box>
      <Box
        sx={{
          bgcolor: theme.palette.background.default,
          borderRadius: 1,
          p: 3,
        }}
      >
        {component?.description && (
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 3 }}>
            {component.description}
          </Typography>
        )}
        <SessionConverterParametersTable
          converter={converter}
          scopeLabel={scopeLabel}
          converterLabel={converterLabel}
          outputSlots={outputSlots}
          t={t}
          theme={theme}
          localization={localization}
        />
      </Box>
    </Paper>
  );
}

/**
 * Center-panel content for the session wizard's preprocessing step: a card
 * per entry already in `session.converters`, each removable. Mirrors the
 * notebook feature's own tool-card pattern; adding a converter happens from
 * the sidebar (SessionConvertersRightBar), this component only renders
 * what's already configured and lets the user remove one. There is no data
 * preview here — converters are no longer applied for real at this point in
 * the wizard (only their configuration is stored), so there is no
 * intermediate dataset to show.
 *
 * Removing a converter cascades to every converter applied after it (a
 * later converter may have been scoped against columns this one produced),
 * matching the notebook's own converter deletion — confirmed first via the
 * same `DeleteConfirmationModal` + `ItemsToDeleteList` notebooks use, so
 * the user sees exactly what else is about to go.
 *
 * Fetches the full `Converter` component list once (same
 * `getComponents({selectTypes: ["Converter"]})` call `SessionConvertersRightBar`/
 * `SessionInfoContent` already make) so a converter's `input_scope` "group"
 * atoms — referencing an *earlier* converter's declared output slot — can
 * be resolved to a readable "ConverterName: slot label" string instead of
 * a raw internal id (see `formatScopeAtom`).
 */
export default function AppliedConvertersView({ session, onRemoveConverter }) {
  const { t } = useTranslation(["models", "datasets", "common"]);
  const converters = session.converters || [];
  const [deleteIndex, setDeleteIndex] = useState(null);
  const [converterTools, setConverterTools] = useState([]);
  const [outputSlotsByConverterId, setOutputSlotsByConverterId] = useState({});

  useEffect(() => {
    let cancelled = false;
    getComponents({ selectTypes: ["Converter"] })
      .then((data) => {
        if (!cancelled) setConverterTools(data || []);
      })
      .catch((error) => {
        console.error("Error fetching converter tools:", error);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Real output slots for each configured converter, from its own actual
  // params (e.g. a `SimpleImputer` configured with `add_indicator: true`
  // really declares a second slot) — see `getConvertersOutputSlots`.
  useEffect(() => {
    let cancelled = false;
    if (!converters.length) {
      setOutputSlotsByConverterId({});
      return undefined;
    }
    getConvertersOutputSlots(converters)
      .then((data) => {
        if (!cancelled) setOutputSlotsByConverterId(data || {});
      })
      .catch((error) => {
        console.error("Error fetching converters' output slots:", error);
      });
    return () => {
      cancelled = true;
    };
  }, [converters]);

  const itemsToDelete = useMemo(() => {
    if (deleteIndex === null) return [];
    return converters.slice(deleteIndex).map((converter, i) => ({
      id: deleteIndex + i,
      type: "converter",
      converter: converter.converter,
    }));
  }, [converters, deleteIndex]);

  const handleConfirmDelete = () => {
    onRemoveConverter(deleteIndex);
    setDeleteIndex(null);
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {converters.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t("models:label.noConvertersAdded")}
          </Typography>
        ) : (
          converters.map((converter, index) => {
            const scope = converter.input_scope || [];
            const scopeLabel =
              scope.length === 0
                ? t("common:all")
                : scope
                    .map((atom) =>
                      formatScopeAtom(atom, converters, converterTools, t),
                    )
                    .join(", ");
            return (
              <SessionConverterCard
                key={`${converter.converter}-${index}`}
                converter={converter}
                scopeLabel={scopeLabel}
                outputSlots={outputSlotsByConverterId[converter.id] || []}
                onDelete={() => setDeleteIndex(index)}
              />
            );
          })
        )}
      </Box>

      <DeleteConfirmationModal
        open={deleteIndex !== null}
        onClose={() => setDeleteIndex(null)}
        onConfirm={handleConfirmDelete}
        content={
          <Box>
            <Typography>
              {t("models:label.deleteConverterConfirmation", {
                converter: converters[deleteIndex]?.converter,
              })}
            </Typography>
            <ItemsToDeleteList items={itemsToDelete} />
          </Box>
        }
      />
    </Box>
  );
}

SessionConverterCard.propTypes = {
  converter: PropTypes.shape({
    converter: PropTypes.string.isRequired,
    input_scope: PropTypes.arrayOf(PropTypes.object),
    target_column: PropTypes.string,
  }).isRequired,
  scopeLabel: PropTypes.string.isRequired,
  outputSlots: PropTypes.arrayOf(
    PropTypes.shape({
      slot: PropTypes.number.isRequired,
      label: PropTypes.string.isRequired,
      type: PropTypes.string,
    }),
  ),
  onDelete: PropTypes.func.isRequired,
};

ConverterOutputChips.propTypes = {
  converterLabel: PropTypes.string.isRequired,
  outputSlots: PropTypes.arrayOf(
    PropTypes.shape({
      slot: PropTypes.number.isRequired,
      label: PropTypes.string.isRequired,
      type: PropTypes.string,
    }),
  ),
};

AppliedConvertersView.propTypes = {
  session: PropTypes.object.isRequired,
  onRemoveConverter: PropTypes.func.isRequired,
};
