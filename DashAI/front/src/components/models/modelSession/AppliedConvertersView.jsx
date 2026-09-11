import React, { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Paper,
  Typography,
  Chip,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  MaterialReactTable,
  useMaterialReactTable,
} from "material-react-table";
import DeleteIcon from "@mui/icons-material/Delete";
import Transform from "@mui/icons-material/Transform";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { getColorByColumnType } from "../../../utils";
import { getComponents } from "../../../api/component";
import { useTableLocalization } from "../../../utils/useTableLocalization";
import DeleteConfirmationModal from "../../threeSectionLayout/DeleteConfirmationModal";
import ItemsToDeleteList from "../../notebooks/converter/ItemsToDeleteList";
import { useExplorersAndConverters } from "../../notebooks/context/ExplorersAndConvertersContext";
import {
  buildColumnKeysAndTypes,
  buildStepDisplayNames,
  groupKey,
  refToKey,
} from "./sessionColumnRefs";

function TypeChip({ type }) {
  if (!type) return null;
  return (
    <Chip
      label={type}
      size="small"
      sx={{
        backgroundColor: (theme) => getColorByColumnType(type, theme),
        color: "#fff",
        fontWeight: 600,
        fontSize: "0.65rem",
        height: "18px",
        ml: 1,
      }}
    />
  );
}

TypeChip.propTypes = { type: PropTypes.string };

function RefChip({ refKey, label, columnTypes }) {
  return (
    <Chip
      size="small"
      label={
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <span>{label}</span>
          <TypeChip type={columnTypes[refKey]?.type} />
        </Box>
      }
    />
  );
}

RefChip.propTypes = {
  refKey: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  columnTypes: PropTypes.object.isRequired,
};

/**
 * Mirrors the notebook's own ConverterParametersTable (same columns, same
 * MaterialReactTable setup): a compact two-column table with one row per
 * converter attribute, values rendered as wrapped chips (each with a
 * colored type badge) instead of plain text, since a session converter's
 * scope/output are references to columns or groups, not literal strings.
 */
function SessionConverterParametersTable({
  step,
  optionLabels,
  columnTypes,
  outputEntries,
  t,
  localization,
}) {
  const paramColumns = [
    { accessorKey: "key", header: t("common:parameter"), grow: 1 },
    { accessorKey: "value", header: t("common:value"), grow: 4 },
  ];

  const paramRows = [
    {
      // Plain comma-joined text, matching the notebook's own
      // ConverterParametersTable (ConverterBox.jsx) — no chips here, since
      // that's how Notebooks shows an already-applied converter's scope.
      key: t("datasets:label.scopeColumns"),
      value: step.scope
        .map((ref) => {
          const key = refToKey(ref);
          return optionLabels[key] || key;
        })
        .join(", "),
    },
    {
      // Usually one chip; more than one when this step's scope mixed
      // column types (e.g. SimpleImputer preserving both a categorical and
      // a numeric column), so each declared slot gets its own chip.
      key: t("datasets:label.converterOutput"),
      value: (
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
          {outputEntries.map(({ key, label }) => (
            <RefChip
              key={key}
              refKey={key}
              label={label}
              columnTypes={columnTypes}
            />
          ))}
        </Box>
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

SessionConverterParametersTable.propTypes = {
  step: PropTypes.object.isRequired,
  optionLabels: PropTypes.object.isRequired,
  columnTypes: PropTypes.object.isRequired,
  outputEntries: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
    }),
  ).isRequired,
  t: PropTypes.func.isRequired,
  localization: PropTypes.object.isRequired,
};

/**
 * A single applied-converter card, styled after the notebook's own
 * ConverterBox (icon + real component display name + description +
 * parameters table), but built against the session's preprocessing step
 * shape (`{converter, scope, outputSlots}`) instead of the notebook's
 * (`{parameters: {scope, target}}`), and with a "Salida" row showing the
 * converter's declared output type(s) — usually one chip, more than one
 * when the step's scope mixed column types — since that group doesn't
 * exist as a real column until the session is created.
 */
function SessionConverterCard({
  step,
  index,
  displayName,
  description,
  onDelete,
  datasetTypes,
  preprocessing,
  stepDisplayNames,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["datasets", "models", "common"]);
  const localization = useTableLocalization();

  const { columnTypes } = buildColumnKeysAndTypes({
    datasetTypes,
    preprocessing,
  });
  // Every earlier step's group label(s) use its resolved display name (e.g.
  // "Bag of Words: output"), matching this card's own output label(s)
  // below — not the raw registry name buildColumnKeysAndTypes falls back
  // to when it has no display-name lookup of its own. One label per
  // declared slot, so a step whose scope mixed types (more than one slot)
  // gets one distinguishable label per slot.
  const optionLabels = {};
  preprocessing.forEach((s, i) => {
    const name = stepDisplayNames[i];
    const slots = s.outputSlots?.length > 0 ? s.outputSlots : [{ slot: null }];
    // No "(slot)" suffix here: RefChip already shows the slot's type as its
    // own colored badge right next to this label, so repeating it as text
    // would be redundant (a step with several slots gets several chips
    // with identical text but different badges, which is enough to tell
    // them apart).
    slots.forEach(({ slot }) => {
      const key = groupKey(i, slot);
      optionLabels[key] = `${name}: output`;
    });
  });
  const ownSlots =
    step.outputSlots?.length > 0 ? step.outputSlots : [{ slot: null }];
  const outputEntries = ownSlots.map(({ slot }) => {
    const key = groupKey(index, slot);
    return { key, label: optionLabels[key] || `${displayName}: output` };
  });

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 4,
        mb: 2,
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
          <Typography variant="subtitle2">{displayName}</Typography>
        </Box>
        <Tooltip title={t("common:delete")}>
          <IconButton
            size="small"
            color="error"
            onClick={() => onDelete(index)}
            aria-label={t("common:remove")}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      <Box
        sx={{
          bgcolor: theme.palette.background.default,
          borderRadius: 1,
          p: 3,
        }}
      >
        {description && (
          <Typography variant="body2" sx={{ color: "text.secondary", mb: 3 }}>
            {description}
          </Typography>
        )}
        <SessionConverterParametersTable
          step={step}
          optionLabels={optionLabels}
          columnTypes={columnTypes}
          outputEntries={outputEntries}
          t={t}
          localization={localization}
        />
      </Box>
    </Paper>
  );
}

SessionConverterCard.propTypes = {
  step: PropTypes.object.isRequired,
  index: PropTypes.number.isRequired,
  displayName: PropTypes.string.isRequired,
  description: PropTypes.string,
  onDelete: PropTypes.func.isRequired,
  datasetTypes: PropTypes.object,
  preprocessing: PropTypes.array,
  stepDisplayNames: PropTypes.arrayOf(PropTypes.string).isRequired,
};

/**
 * Cards for every converter already added to the session's preprocessing
 * sequence, mirroring the notebook module's applied-tool cards.
 *
 * Deleting a converter cascades: any later converter whose scope
 * references its output group would be left pointing at a step that no
 * longer exists, so every converter configured after it is removed too.
 * Confirmed first via the same `DeleteConfirmationModal` +
 * `ItemsToDeleteList` the notebook's own converter deletion uses, so the
 * user sees exactly what else is about to go before confirming.
 */
export default function AppliedConvertersView({
  newExp,
  setNewExp,
  datasetTypes,
}) {
  const { t } = useTranslation(["experiments", "models", "datasets", "common"]);
  const theme = useTheme();
  const { setPendingDropTool } = useExplorersAndConverters();
  const [convertersMeta, setConvertersMeta] = useState({});
  const [deleteIndex, setDeleteIndex] = useState(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const steps = newExp.preprocessing || [];

  // A converter is draggable from SessionConvertersRightBar's ToolList/
  // ToolGrid for free (drag-start lives in the shared ToolListItem/
  // ToolGridItem, not in those wrappers), so this view only needs to be a
  // drop target — same "application/x-dashai-tool" payload and the same
  // setPendingDropTool hand-off Notebooks' own NotebookView.jsx uses, which
  // ToolList/ToolGrid already resolve through their normal click-to-add path.
  useEffect(() => {
    const onStart = (e) => {
      if (e.dataTransfer.types.includes("application/x-dashai-tool")) {
        setIsDragging(true);
      }
    };
    const onEnd = () => {
      setIsDragging(false);
      setIsDragOver(false);
    };
    window.addEventListener("dragstart", onStart);
    window.addEventListener("dragend", onEnd);
    return () => {
      window.removeEventListener("dragstart", onStart);
      window.removeEventListener("dragend", onEnd);
    };
  }, []);

  const handleDragOver = (e) => {
    if (!e.dataTransfer.types.includes("application/x-dashai-tool")) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
  };

  const handleDragEnter = (e) => {
    if (!e.dataTransfer.types.includes("application/x-dashai-tool")) return;
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    const related = e.relatedTarget;
    if (!related || !e.currentTarget.contains(related)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    try {
      const tool = JSON.parse(
        e.dataTransfer.getData("application/x-dashai-tool"),
      );
      if (tool?.name) setPendingDropTool(tool);
    } catch {
      // ignore invalid drops
    }
  };

  useEffect(() => {
    let cancelled = false;
    getComponents({ selectTypes: ["Converter"] })
      .then((data) => {
        if (cancelled) return;
        const byName = Object.fromEntries(
          (data || []).map((component) => [component.name, component]),
        );
        setConvertersMeta(byName);
      })
      .catch((error) =>
        console.error("Failed to fetch converter metadata:", error),
      );
    return () => {
      cancelled = true;
    };
  }, []);

  // Numbers duplicate converter types ("Simple Imputer" / "Simple Imputer
  // (2)") so two steps of the same type never render with identical names
  // — see buildStepDisplayNames.
  const stepDisplayNames = buildStepDisplayNames(steps, convertersMeta);

  const itemsToDelete = useMemo(() => {
    if (deleteIndex === null) return [];
    return steps.slice(deleteIndex).map((step, i) => ({
      id: deleteIndex + i,
      type: "converter",
      converter: stepDisplayNames[deleteIndex + i],
    }));
  }, [steps, deleteIndex, stepDisplayNames]);

  const handleConfirmDelete = () => {
    setNewExp({
      ...newExp,
      preprocessing: steps.slice(0, deleteIndex),
    });
    setDeleteIndex(null);
  };

  return (
    <Box
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      sx={{
        position: "relative",
        // A percentage minHeight is unreliable here — this Box is a flex
        // item inside CreateSessionSteps' flex-column scroll container, and
        // percentage heights don't resolve dependably through it. flex: 1
        // makes it actually fill the remaining vertical space (with content
        // shorter than the panel, e.g. the empty state or few cards), so the
        // drop-target outline/overlay below is a full square instead of a
        // sliver hugging just the content's own height.
        flex: 1,
        outline: isDragOver
          ? `2px dashed ${theme.palette.primary.main}`
          : isDragging
            ? `2px dashed ${theme.palette.divider}`
            : "none",
        transition: "outline 0.15s",
      }}
    >
      {isDragging && (
        <Box
          sx={{
            position: "absolute",
            inset: 0,
            zIndex: 10,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            bgcolor: isDragOver
              ? `${theme.palette.primary.main}14`
              : theme.palette.action.hover,
            pointerEvents: "none",
            transition: "background-color 0.15s",
          }}
        >
          <Typography
            variant="h6"
            sx={{
              color: isDragOver
                ? theme.palette.primary.main
                : theme.palette.text.secondary,
              fontWeight: 600,
              pointerEvents: "none",
              transition: "color 0.15s",
            }}
          >
            {t("datasets:label.dropToolHere")}
          </Typography>
        </Box>
      )}

      {steps.length === 0 ? (
        <Typography variant="body2" sx={{ color: "grey" }}>
          {t("experiments:label.noConverterAdded")}
        </Typography>
      ) : (
        steps.map((step, index) => {
          const meta = convertersMeta[step.converter];
          return (
            <SessionConverterCard
              key={`${step.converter}-${index}`}
              step={step}
              index={index}
              displayName={stepDisplayNames[index]}
              description={
                meta?.description || meta?.metadata?.short_description
              }
              onDelete={(i) => setDeleteIndex(i)}
              datasetTypes={datasetTypes}
              preprocessing={steps}
              stepDisplayNames={stepDisplayNames}
            />
          );
        })
      )}

      <DeleteConfirmationModal
        open={deleteIndex !== null}
        onClose={() => setDeleteIndex(null)}
        onConfirm={handleConfirmDelete}
        content={
          <Box>
            <Typography>
              {t("datasets:label.deleteConverterConfirmation", {
                converter: stepDisplayNames[deleteIndex],
              })}
            </Typography>
            <ItemsToDeleteList items={itemsToDelete} />
          </Box>
        }
      />
    </Box>
  );
}

AppliedConvertersView.propTypes = {
  newExp: PropTypes.object.isRequired,
  setNewExp: PropTypes.func.isRequired,
  datasetTypes: PropTypes.object,
};
