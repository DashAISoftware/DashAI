import React, { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
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
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
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
  buildStepDisplayNames,
  labelForRef,
  stateToOptions,
} from "./sessionColumnRefs";
import { formatStructureMessage } from "./structureMessages";

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

function RefChip({ label, type }) {
  return (
    <Chip
      size="small"
      label={
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <span>{label}</span>
          <TypeChip type={type} />
        </Box>
      }
    />
  );
}

RefChip.propTypes = {
  label: PropTypes.string.isRequired,
  type: PropTypes.string,
};

/**
 * One chip per item of an estimated dataset state: an original column shows
 * its name, anything a step produced shows its label (a block also shows its
 * column count, "N" when only known after fit).
 */
function StateChips({ items, stepDisplayNames }) {
  const { t } = useTranslation(["models"]);
  const { allKeys, columnTypes, optionLabels } = stateToOptions(
    items,
    stepDisplayNames,
    t,
  );
  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
      {allKeys.map((key) => (
        <RefChip
          key={key}
          label={optionLabels[key] || key}
          type={columnTypes[key]?.type}
        />
      ))}
    </Box>
  );
}

StateChips.propTypes = {
  items: PropTypes.array.isRequired,
  stepDisplayNames: PropTypes.arrayOf(PropTypes.string).isRequired,
};

/**
 * Mirrors the notebook's own ConverterParametersTable (same columns, same
 * MaterialReactTable setup): a compact two-column table with one row per
 * converter attribute. The scope is plain text, like Notebooks shows an
 * applied converter's scope; the output is one chip per column or block the
 * step produces, each with its type.
 */
function SessionConverterParametersTable({
  step,
  added,
  stepDisplayNames,
  t,
  localization,
}) {
  const paramColumns = [
    { accessorKey: "key", header: t("common:parameter"), grow: 1 },
    { accessorKey: "value", header: t("common:value"), grow: 4 },
  ];

  const paramRows = [
    {
      key: t("datasets:label.scopeColumns"),
      value: step.scope
        .map((ref) => labelForRef(ref, stepDisplayNames, t))
        .join(", "),
    },
    {
      key: t("datasets:label.converterOutput"),
      value: <StateChips items={added} stepDisplayNames={stepDisplayNames} />,
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
  added: PropTypes.array.isRequired,
  stepDisplayNames: PropTypes.arrayOf(PropTypes.string).isRequired,
  t: PropTypes.func.isRequired,
  localization: PropTypes.object.isRequired,
};

/**
 * A single applied-converter card, styled after the notebook's own
 * ConverterBox (icon + real component display name + description +
 * parameters table), built against the session's preprocessing step shape
 * (`{converter, params, scope}`). Its output and status come from the
 * chain's estimated structure: a step that cannot work is outlined in red
 * with the reason, a step after it is dimmed (it cannot be checked until
 * the earlier one is fixed), and warnings are shown under the table.
 */
function SessionConverterCard({
  step,
  index,
  displayName,
  description,
  onDelete,
  stepStructure,
  stepDisplayNames,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["datasets", "models", "common"]);
  const localization = useTableLocalization();
  const status = stepStructure?.status;

  return (
    <Paper
      variant="outlined"
      data-testid={`session-converter-card-${index}`}
      data-status={status || "pending"}
      sx={{
        p: 4,
        mb: 2,
        bgcolor: "background.paper",
        borderColor:
          status === "error"
            ? theme.palette.error.main
            : theme.palette.ui.border,
        borderRadius: 1,
        opacity: status === "blocked" ? 0.6 : 1,
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
      {status === "error" && (
        <Typography variant="body2" sx={{ color: "error.main", mb: 3 }}>
          {formatStructureMessage(t, stepStructure.error)}
        </Typography>
      )}
      {status === "blocked" && (
        <Typography variant="body2" sx={{ color: "text.secondary", mb: 3 }}>
          {t("models:structure.blocked")}
        </Typography>
      )}
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
          added={stepStructure?.added || []}
          stepDisplayNames={stepDisplayNames}
          t={t}
          localization={localization}
        />
        {(stepStructure?.warnings || []).map((warning, i) => (
          <Typography
            key={`${warning.code}-${i}`}
            variant="caption"
            component="p"
            sx={{ color: "text.secondary", mt: 2 }}
          >
            {formatStructureMessage(t, warning)}
          </Typography>
        ))}
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
  stepStructure: PropTypes.object,
  stepDisplayNames: PropTypes.arrayOf(PropTypes.string).isRequired,
};

/**
 * The estimated dataset state at the end of the chain: what the model
 * inputs will be picked from in the next step.
 */
function DatasetStatePanel({ finalState, stepDisplayNames }) {
  const { t } = useTranslation(["models"]);
  return (
    <Accordion defaultExpanded disableGutters variant="outlined" sx={{ mb: 3 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle2">
          {t("models:structure.currentState")}
        </Typography>
      </AccordionSummary>
      <AccordionDetails>
        <StateChips items={finalState} stepDisplayNames={stepDisplayNames} />
      </AccordionDetails>
    </Accordion>
  );
}

DatasetStatePanel.propTypes = {
  finalState: PropTypes.array.isRequired,
  stepDisplayNames: PropTypes.arrayOf(PropTypes.string).isRequired,
};

/**
 * Cards for every converter already added to the session's preprocessing
 * sequence, mirroring the notebook module's applied-tool cards, under a
 * panel with the estimated dataset state after the whole chain.
 *
 * Deleting a converter cascades: any later converter could reference what
 * it produces and would be left pointing at a step that no longer exists,
 * so every converter configured after it is removed too. Confirmed first
 * via the same `DeleteConfirmationModal` + `ItemsToDeleteList` the
 * notebook's own converter deletion uses, so the user sees exactly what
 * else is about to go before confirming.
 */
export default function AppliedConvertersView({
  newExp,
  setNewExp,
  structure,
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
  // drop target: same "application/x-dashai-tool" payload and the same
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
  // (see buildStepDisplayNames).
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
        // A percentage minHeight is unreliable here: this Box is a flex
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

      {structure && (
        <DatasetStatePanel
          finalState={structure.final}
          stepDisplayNames={stepDisplayNames}
        />
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
              stepStructure={structure?.steps?.[index]}
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
  // The chain's estimated structure (see usePreprocessingStructure); null
  // until the first estimate arrives.
  structure: PropTypes.object,
};
