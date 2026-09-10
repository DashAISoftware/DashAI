import React, { useState, useRef } from "react";
import PropTypes from "prop-types";
import { useTheme } from "@mui/material/styles";
import Plot from "react-plotly.js";
import { Box, IconButton, Tooltip, Menu, MenuItem } from "@mui/material";
import Dialog from "@mui/material/Dialog";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import ZoomOutIcon from "@mui/icons-material/ZoomOut";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import FullscreenExitIcon from "@mui/icons-material/FullscreenExit";
import FileDownloadOutlinedIcon from "@mui/icons-material/FileDownloadOutlined";
import { buildAxisResetUpdate } from "../../../../utils/plotlyAxes";
import { buildPlotMargin } from "../../../../utils/plotlyMargin";

const MIN_WIDTH = 300;
const MIN_HEIGHT_MINIMALIST = 200;
const MIN_HEIGHT_NORMAL = 500;

function PlotlyJsonVisualizer({
  data,
  minimalist = false,
  fillHeight = false,
}) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);
  // Which plot ref + anchor the download format menu (PNG/SVG) applies to.
  const [downloadMenu, setDownloadMenu] = useState(null);
  const plotRef = useRef(null);
  const fullscreenPlotRef = useRef(null);

  // Increment revision whenever data reference changes to force Plotly.react
  const revisionRef = useRef(0);
  const prevDataRef = useRef(null);
  if (prevDataRef.current !== data) {
    revisionRef.current += 1;
    prevDataRef.current = data;
  }

  // Parse JSON if data is a string
  const parsedData = typeof data === "string" ? JSON.parse(data) : data;

  const plotData = minimalist
    ? {
        ...parsedData,
        layout: {
          ...parsedData.layout,
          title: "",
        },
      }
    : fillHeight
      ? { ...parsedData, layout: { ...parsedData.layout } }
      : {
          ...parsedData,
          layout: { ...parsedData.layout, height: MIN_HEIGHT_NORMAL },
        };

  const getPlotly = (ref) => {
    const el = ref?.current?.el;
    if (!el) return null;
    return (
      el._fullLayout?._context?._exportedPlotly ||
      el._fullData?.[0]?._fullLayout?._context?._exportedPlotly ||
      window.Plotly ||
      null
    );
  };

  const relayout = (ref, update) => {
    const el = ref?.current?.el;
    const Plotly = getPlotly(ref);
    if (el && Plotly) Plotly.relayout(el, update);
  };

  const handleZoomIn = (ref) => {
    const el = ref?.current?.el;
    if (!el) return;
    const xRange = el._fullLayout?.xaxis?.range;
    const yRange = el._fullLayout?.yaxis?.range;
    if (xRange && yRange) {
      const xCenter = (xRange[0] + xRange[1]) / 2;
      const yCenter = (yRange[0] + yRange[1]) / 2;
      const xSpan = (xRange[1] - xRange[0]) * 0.25;
      const ySpan = (yRange[1] - yRange[0]) * 0.25;
      relayout(ref, {
        "xaxis.range": [xCenter - xSpan, xCenter + xSpan],
        "yaxis.range": [yCenter - ySpan, yCenter + ySpan],
      });
    }
  };

  const handleZoomOut = (ref) => {
    const el = ref?.current?.el;
    if (!el) return;
    const xRange = el._fullLayout?.xaxis?.range;
    const yRange = el._fullLayout?.yaxis?.range;
    if (xRange && yRange) {
      const xCenter = (xRange[0] + xRange[1]) / 2;
      const yCenter = (yRange[0] + yRange[1]) / 2;
      const xSpan = (xRange[1] - xRange[0]) * 0.75;
      const ySpan = (yRange[1] - yRange[0]) * 0.75;
      relayout(ref, {
        "xaxis.range": [xCenter - xSpan, xCenter + xSpan],
        "yaxis.range": [yCenter - ySpan, yCenter + ySpan],
      });
    }
  };

  const handleReset = (ref) => {
    const el = ref?.current?.el;
    if (!el) return;
    // Mirrors the zoom handlers above, which already bail when the figure has
    // no cartesian axes. Parallel coordinates, pie and polar figures have
    // none, and autoranging an axis that does not exist throws inside Plotly.
    const update = buildAxisResetUpdate(el._fullLayout);
    if (update) relayout(ref, update);
  };

  const handleDownload = (ref, format = "svg") => {
    const el = ref?.current?.el;
    const Plotly = getPlotly(ref);
    if (el && Plotly) {
      Plotly.downloadImage(el, {
        format,
        filename: "dashai-plot",
        height: 800,
        width: 1200,
        scale: 1,
      });
    }
  };

  // Fall back to the app theme when the figure does not pin its own colors,
  // so a computed plot tracks light/dark while a user edited one keeps the
  // colors it was saved with.
  const themeBg = theme.palette.background.paper;
  const themeText = theme.palette.text.primary;
  const themeGrid = theme.palette.divider;

  const plotConfig = {
    responsive: true,
    displaylogo: false,
    displayModeBar: false,
  };

  const plotLayout = {
    ...plotData.layout,
    paper_bgcolor: plotData.layout?.paper_bgcolor || themeBg,
    plot_bgcolor: plotData.layout?.plot_bgcolor || themeBg,
    margin: {
      ...buildPlotMargin(plotData, minimalist),
      ...plotData.layout?.margin,
    },
    autosize: true,
    font: {
      size: minimalist ? 10 : 12,
      color: themeText,
      ...plotData.layout?.font,
    },
    xaxis: {
      gridcolor: themeGrid,
      zerolinecolor: themeGrid,
      ...plotData.layout?.xaxis,
    },
    yaxis: {
      gridcolor: themeGrid,
      zerolinecolor: themeGrid,
      ...plotData.layout?.yaxis,
    },
    title: {
      ...plotData.layout?.title,
      font: {
        size: minimalist ? 12 : 16,
        color: themeText,
        ...plotData.layout?.title?.font,
      },
    },
  };

  const iconBtnSx = {
    bgcolor: theme.palette.background.paper,
    border: `1px solid ${theme.palette.ui.borderLight}`,
    color: theme.palette.text.disabled,
    width: 30,
    height: 30,
    "&:hover": {
      bgcolor: theme.palette.background.paper,
      color: theme.palette.text.secondary,
    },
  };

  const downloadBtnSx = {
    bgcolor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    width: 30,
    height: 30,
    "&:hover": {
      bgcolor: theme.palette.primary.light,
    },
  };

  const ToolbarButtons = ({
    plotRefProp,
    showFullscreenExit = false,
    compact = false,
  }) => (
    <Box
      sx={{
        position: "absolute",
        top: 8,
        right: 8,
        zIndex: 2,
        display: "flex",
        alignItems: "center",
        gap: 1,
      }}
    >
      {!compact && (
        <>
          <Tooltip title="Zoom in" arrow>
            <IconButton
              size="small"
              onClick={() => handleZoomIn(plotRefProp)}
              sx={iconBtnSx}
            >
              <ZoomInIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Zoom out" arrow>
            <IconButton
              size="small"
              onClick={() => handleZoomOut(plotRefProp)}
              sx={iconBtnSx}
            >
              <ZoomOutIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
          <Tooltip title="Reset axes" arrow>
            <IconButton
              size="small"
              onClick={() => handleReset(plotRefProp)}
              sx={iconBtnSx}
            >
              <RestartAltIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Tooltip>
        </>
      )}
      {showFullscreenExit ? (
        <Tooltip title="Exit fullscreen" arrow>
          <IconButton
            size="small"
            onClick={() => setExpanded(false)}
            sx={iconBtnSx}
          >
            <FullscreenExitIcon sx={{ fontSize: 18 }} />
          </IconButton>
        </Tooltip>
      ) : (
        <Tooltip title="Fullscreen" arrow>
          <IconButton
            size="small"
            onClick={() => setExpanded(true)}
            sx={iconBtnSx}
          >
            <FullscreenIcon sx={{ fontSize: 18 }} />
          </IconButton>
        </Tooltip>
      )}
      <Tooltip title="Download" arrow>
        <IconButton
          size="small"
          onClick={(e) =>
            setDownloadMenu({
              mouseX: e.clientX,
              mouseY: e.clientY,
              ref: plotRefProp,
            })
          }
          sx={downloadBtnSx}
        >
          <FileDownloadOutlinedIcon sx={{ fontSize: 18 }} />
        </IconButton>
      </Tooltip>
    </Box>
  );

  return (
    <React.Fragment>
      <Box
        sx={{
          position: "relative",
          width: "100%",
          minWidth: MIN_WIDTH,
          minHeight: fillHeight
            ? 0
            : minimalist
              ? MIN_HEIGHT_MINIMALIST
              : MIN_HEIGHT_NORMAL,
          height: minimalist || fillHeight ? "100%" : "auto",
          overflow: "hidden",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <ToolbarButtons plotRefProp={plotRef} compact={minimalist} />
        {!expanded ? (
          <Plot
            ref={plotRef}
            id="plotly-graph"
            data={plotData.data}
            layout={plotLayout}
            revision={revisionRef.current}
            style={{
              width: "100%",
              minHeight: fillHeight
                ? 0
                : minimalist
                  ? MIN_HEIGHT_MINIMALIST
                  : MIN_HEIGHT_NORMAL,
              height: minimalist || fillHeight ? "100%" : MIN_HEIGHT_NORMAL,
            }}
            config={plotConfig}
            useResizeHandler={true}
          />
        ) : (
          <Dialog
            open={expanded}
            fullScreen
            onClose={() => setExpanded(false)}
            slotProps={{
              paper: {
                sx: { bgcolor: "background.default" },
              },
            }}
          >
            <Box sx={{ position: "relative", width: "100%", height: "100%" }}>
              <ToolbarButtons
                plotRefProp={fullscreenPlotRef}
                showFullscreenExit
              />
              <Plot
                ref={fullscreenPlotRef}
                data={plotData.data}
                layout={{
                  ...plotData.layout,
                  paper_bgcolor: plotData.layout?.paper_bgcolor || themeBg,
                  plot_bgcolor: plotData.layout?.plot_bgcolor || themeBg,
                  autosize: true,
                  margin: {
                    l: 80,
                    r: 40,
                    t: 80,
                    b: 80,
                    ...plotData.layout?.margin,
                  },
                  font: {
                    size: 14,
                    color: themeText,
                    ...plotData.layout?.font,
                  },
                  title: {
                    ...plotData.layout?.title,
                    font: {
                      size: 18,
                      color: themeText,
                      ...plotData.layout?.title?.font,
                    },
                  },
                }}
                style={{ width: "100vw", height: "100vh" }}
                useResizeHandler={true}
                config={{ ...plotConfig, scrollZoom: true }}
              />
            </Box>
          </Dialog>
        )}
      </Box>

      <Menu
        open={Boolean(downloadMenu)}
        onClose={() => setDownloadMenu(null)}
        anchorReference="anchorPosition"
        anchorPosition={
          downloadMenu
            ? { top: downloadMenu.mouseY, left: downloadMenu.mouseX }
            : undefined
        }
      >
        <MenuItem
          onClick={() => {
            handleDownload(downloadMenu.ref, "png");
            setDownloadMenu(null);
          }}
        >
          PNG
        </MenuItem>
        <MenuItem
          onClick={() => {
            handleDownload(downloadMenu.ref, "svg");
            setDownloadMenu(null);
          }}
        >
          SVG
        </MenuItem>
      </Menu>
    </React.Fragment>
  );
}

PlotlyJsonVisualizer.propTypes = {
  data: PropTypes.oneOfType([PropTypes.object, PropTypes.string]).isRequired,
  minimalist: PropTypes.bool,
  fillHeight: PropTypes.bool,
};

export default PlotlyJsonVisualizer;
