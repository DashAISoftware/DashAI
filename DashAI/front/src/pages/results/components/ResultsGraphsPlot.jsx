import React, { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import Plot from "react-plotly.js";
import { useTranslation } from "react-i18next";
import { DragIndicator } from "@mui/icons-material";
import PlotActions from "../../../components/shared/PlotActions";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  rectSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

const PANEL_ORDER_STORAGE_KEY = "dashai-results-panel-order";
const HEATMAP_ID = "__heatmap__";
// Matches the run cards grid's minmax floor (SessionVisualization.jsx) so
// both sections switch between 1 and 2 columns at the same container width
// instead of disagreeing in a narrow "dead zone".
const PANEL_MIN_WIDTH = 340;
const GRID_GAP = 24; // gap: 3 → 3 * 8px

function EmptyState({ message }) {
  return (
    <Box
      flex={1}
      display="flex"
      alignItems="center"
      justifyContent="center"
      sx={{
        minHeight: 400,
        border: "1px dashed",
        borderColor: "divider",
        borderRadius: 1,
        m: 4,
      }}
    >
      <Typography color="text.secondary">{message}</Typography>
    </Box>
  );
}

/**
 * One draggable card (a metric panel or the heatmap) — the drag handle is a
 * small grip icon next to the title, so dragging never conflicts with
 * hovering/clicking the plot itself (Plotly needs mouse events for its own
 * hover tooltips).
 */
function SortableCard({
  id,
  title,
  gridColumn,
  plotData,
  plotLayout,
  children,
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });
  const containerRef = useRef(null);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    gridColumn,
  };

  return (
    <Box
      ref={(node) => {
        setNodeRef(node);
        containerRef.current = node;
      }}
      style={style}
      sx={{
        border: 1,
        borderColor: "divider",
        borderRadius: 1,
        p: 2,
        "& .plot-actions": { opacity: 0, transition: "opacity 0.15s ease" },
        "&:hover .plot-actions, &:focus-within .plot-actions": {
          opacity: 1,
        },
        "@media (hover: none)": {
          "& .plot-actions": { opacity: 1 },
        },
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          mb: 1,
          px: 1,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Box
            {...attributes}
            {...listeners}
            sx={{
              display: "flex",
              alignItems: "center",
              color: "text.disabled",
              cursor: "grab",
              "&:active": { cursor: "grabbing" },
              "&:hover": { color: "text.secondary" },
            }}
          >
            <DragIndicator fontSize="small" />
          </Box>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            {title}
          </Typography>
        </Box>
        <PlotActions
          getContainer={() => containerRef.current}
          data={plotData}
          layout={plotLayout}
          filename={title}
        />
      </Box>
      {children}
    </Box>
  );
}

function ResultsGraphsPlot({ chartData, onToggleRun, sessionId }) {
  const { t } = useTranslation(["models"]);
  const theme = useTheme();
  const bgColor = theme.palette.background.paper;
  const textColor = theme.palette.text.primary;
  const gridColor = theme.palette.divider;

  const panels = chartData.bar ?? [];
  const legend = chartData.legend ?? [];
  const yaxis = chartData.yaxis;
  const heatmapData = chartData.heatmap ?? [];

  // Scoped per session — otherwise dragging a card in one session's Graphs
  // would silently reorder every other session's Graphs too, since it's the
  // same metric/heatmap ids everywhere. The parent remounts this component
  // (via `key={sessionId}`) whenever the session changes, so this only needs
  // to be read once per mount.
  const storageKey = sessionId
    ? `${PANEL_ORDER_STORAGE_KEY}-${sessionId}`
    : PANEL_ORDER_STORAGE_KEY;

  const [order, setOrder] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Every draggable card — one per metric panel, plus the heatmap.
  const cardIds = panels
    .map((p) => p.metric)
    .concat(heatmapData.length > 0 ? [HEATMAP_ID] : []);

  // Keep the stored order in sync with whatever cards are actually being
  // shown right now — known cards keep their saved (customized) relative
  // order; newly-seen ones are inserted at the natural position they'd have
  // had if nothing were customized (i.e. right before whichever known card
  // naturally comes after them), not always shoved to the very end. Without
  // this, a heatmap dragged ahead of a single metric would permanently trap
  // every later-appearing metric behind it, since "appended at the end"
  // means "after the heatmap" too — which is exactly what made the heatmap's
  // position look inconsistent across sessions.
  const cardIdsKey = cardIds.join("|");
  useEffect(() => {
    // Skip while chart data is still loading (cards momentarily empty) —
    // reconciling against an empty list would wipe the saved order before
    // the real cards ever arrive.
    if (cardIds.length === 0) return;
    setOrder((prev) => {
      const known = prev.filter((id) => cardIds.includes(id));
      const missing = cardIds.filter((id) => !known.includes(id));
      const naturalIndex = new Map(cardIds.map((id, i) => [id, i]));
      const next = [...known];
      missing.forEach((id) => {
        const idx = naturalIndex.get(id);
        const insertAt = next.findIndex((k) => naturalIndex.get(k) > idx);
        next.splice(insertAt === -1 ? next.length : insertAt, 0, id);
      });
      const unchanged =
        next.length === prev.length && next.every((id, i) => id === prev[i]);
      return unchanged ? prev : next;
    });
  }, [cardIdsKey]);

  useEffect(() => {
    if (order.length > 0) {
      localStorage.setItem(storageKey, JSON.stringify(order));
    }
  }, [order, storageKey]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    setOrder((prev) => {
      const oldIndex = prev.indexOf(active.id);
      const newIndex = prev.indexOf(over.id);
      if (oldIndex === -1 || newIndex === -1) return prev;
      return arrayMove(prev, oldIndex, newIndex);
    });
  };

  // The heatmap spans 2 grid columns, which forces the auto-fill grid to
  // reserve 2 tracks even when the container is too narrow for two real
  // 420px columns — CSS then resolves that shortage by splitting the
  // columns unevenly instead of collapsing to one column per row. Only ask
  // for the 2-column span once the container actually has room for it.
  //
  // Uses a state-backed (not plain useRef) callback ref: the grid only
  // mounts once chartData finishes loading (before that, EmptyState renders
  // instead), so a plain ref + `useEffect(..., [])` would fire before the
  // node exists and never re-attach once it does.
  const [gridNode, setGridNode] = useState(null);
  const [canSpanTwoColumns, setCanSpanTwoColumns] = useState(true);

  useEffect(() => {
    if (!gridNode) return undefined;
    const TWO_COLUMN_MIN_WIDTH = PANEL_MIN_WIDTH * 2 + GRID_GAP;
    const observer = new ResizeObserver(([entry]) => {
      setCanSpanTwoColumns(entry.contentRect.width >= TWO_COLUMN_MIN_WIDTH);
    });
    observer.observe(gridNode);
    return () => observer.disconnect();
  }, [gridNode]);

  if (panels.length === 0 && heatmapData.length === 0) {
    return (
      <EmptyState message={t("models:label.noMetricsAvailableForThisView")} />
    );
  }

  const orderedIds = order.filter((id) => cardIds.includes(id));

  const panelLayout = {
    autosize: true,
    height: 240,
    margin: { l: 110, r: 12, t: 8, b: 32 },
    showlegend: false,
    paper_bgcolor: bgColor,
    plot_bgcolor: bgColor,
    bargap: 0.25,
    font: {
      color: textColor,
      family: theme.typography.fontFamily,
      size: 11,
    },
    xaxis: {
      gridcolor: gridColor,
      zerolinecolor: gridColor,
      tickfont: { color: textColor, size: 10 },
    },
    yaxis: {
      gridcolor: gridColor,
      tickfont: { color: textColor, size: 10 },
      automargin: true,
      tickvals: yaxis?.tickvals,
      ticktext: yaxis?.ticktext,
    },
  };

  return (
    <Box sx={{ p: 4, width: "100%" }}>
      {/* Shared legend — one entry per run, same color in every panel */}
      {legend.length > 1 && (
        <Box
          sx={{
            display: "flex",
            flexWrap: "wrap",
            gap: 3,
            mb: 4,
            px: 1,
          }}
        >
          {legend.map(({ id, label, color, hidden }) => (
            <Box
              key={id}
              onClick={() => onToggleRun(id)}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.5,
                cursor: "pointer",
                opacity: hidden ? 0.4 : 1,
                userSelect: "none",
                "&:hover": { opacity: hidden ? 0.65 : 0.8 },
              }}
            >
              <Box
                sx={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  bgcolor: color,
                  flexShrink: 0,
                  filter: hidden ? "grayscale(1)" : "none",
                }}
              />
              <Typography variant="caption" color="text.secondary">
                {label}
              </Typography>
            </Box>
          ))}
        </Box>
      )}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={orderedIds} strategy={rectSortingStrategy}>
          <Box
            ref={setGridNode}
            sx={{
              display: "grid",
              gap: 3,
              gridTemplateColumns: `repeat(auto-fill, minmax(${PANEL_MIN_WIDTH}px, 1fr))`,
            }}
          >
            {orderedIds.map((id) => {
              if (id === HEATMAP_ID) {
                const heatmapLayout = {
                  ...(chartData.generalLayout ?? {}),
                  autosize: true,
                  width: undefined,
                };
                return (
                  <SortableCard
                    key={id}
                    id={id}
                    title={t("models:label.heatmap")}
                    gridColumn={canSpanTwoColumns ? "span 2" : undefined}
                    plotData={heatmapData}
                    plotLayout={heatmapLayout}
                  >
                    <Box sx={{ height: 480 }}>
                      <Plot
                        data={heatmapData}
                        layout={heatmapLayout}
                        useResizeHandler
                        style={{ width: "100%", height: "100%" }}
                        config={{
                          responsive: true,
                          displayModeBar: false,
                          staticPlot: true,
                        }}
                      />
                    </Box>
                  </SortableCard>
                );
              }

              const panel = panels.find((p) => p.metric === id);
              if (!panel) return null;
              return (
                <SortableCard
                  key={id}
                  id={id}
                  title={panel.title}
                  plotData={panel.data}
                  plotLayout={panelLayout}
                >
                  <Plot
                    data={panel.data}
                    layout={panelLayout}
                    useResizeHandler
                    style={{ width: "100%", height: "240px" }}
                    config={{ responsive: true, displayModeBar: false }}
                  />
                </SortableCard>
              );
            })}
          </Box>
        </SortableContext>
      </DndContext>
    </Box>
  );
}

SortableCard.propTypes = {
  id: PropTypes.string.isRequired,
  title: PropTypes.string.isRequired,
  gridColumn: PropTypes.string,
  plotData: PropTypes.array.isRequired,
  plotLayout: PropTypes.object,
  children: PropTypes.node.isRequired,
};

SortableCard.defaultProps = {
  gridColumn: undefined,
};

ResultsGraphsPlot.propTypes = {
  chartData: PropTypes.object.isRequired,
  onToggleRun: PropTypes.func.isRequired,
  sessionId: PropTypes.number,
};

export default ResultsGraphsPlot;
