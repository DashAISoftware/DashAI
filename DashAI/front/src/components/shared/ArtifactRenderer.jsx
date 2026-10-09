import React, { useMemo } from "react";
import { Box, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import Plot from "react-plotly.js";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";

import { applyThemeToLayout } from "../../utils/plotlyTheme";
import TableArtifact from "./TableArtifact";

/**
 * Renders a single typed artifact ({type, payload, title}) returned by the
 * backend (explainer plots, explorer results). Supported types: "plotly"
 * (payload: plotly JSON string), "table" (payload: {columns, rows,
 * highlight}), "image" (payload: {data, mime}) and "text" (payload: string).
 * Unknown types fall back to preformatted text so nothing is silently lost.
 * The optional height sets the plot height and caps image/table height; it
 * lets callers render larger (for example a fullscreen view).
 */
function ArtifactRenderer({ artifact, height = 380 }) {
  const theme = useTheme();
  const { t } = useTranslation(["common"]);

  const parsedFigure = useMemo(() => {
    if (artifact.type !== "plotly") return null;
    try {
      return typeof artifact.payload === "string"
        ? JSON.parse(artifact.payload)
        : artifact.payload;
    } catch (error) {
      console.error("Invalid plotly artifact payload", error);
      return null;
    }
  }, [artifact]);

  const themedLayout = useMemo(() => {
    if (!parsedFigure) return {};
    // User-edited (overridden) figures are rendered verbatim so their saved
    // colors/background survive; only strip fixed sizing. Non-overridden
    // figures follow the app light/dark theme.
    if (artifact.overridden) {
      const { width: _w, height: _h, ...rest } = parsedFigure.layout ?? {};
      return rest;
    }
    return applyThemeToLayout(parsedFigure.layout, theme);
  }, [parsedFigure, theme, artifact.overridden]);

  const highlightedCells = useMemo(() => {
    if (artifact.type !== "table") return new Set();
    const cells = artifact.payload?.highlight ?? [];
    return new Set(cells.map((cell) => `${cell.row}-${cell.column}`));
  }, [artifact]);

  // react-plotly.js diffs by reference, so a fresh layout object on every
  // render sends Plotly through a full relayout. Ancestors re-render often
  // (starting a drag is enough), and each one would otherwise relayout every
  // mounted plot at once.
  const plotLayout = useMemo(
    () => ({ ...themedLayout, height, autosize: true }),
    [themedLayout, height],
  );

  const renderContent = () => {
    switch (artifact.type) {
      case "plotly":
        if (!parsedFigure) return null;
        return (
          <Plot
            data={parsedFigure.data}
            layout={plotLayout}
            config={{ displayModeBar: false }}
            useResizeHandler
            style={{ width: "100%" }}
          />
        );
      case "table": {
        const { columns = [], rows = [] } = artifact.payload ?? {};
        return (
          <TableArtifact
            columns={columns}
            rows={rows}
            highlightedCells={highlightedCells}
            height={height}
          />
        );
      }
      case "image": {
        const { data = "", mime = "image/png" } = artifact.payload ?? {};
        return (
          <Box
            component="img"
            src={`data:${mime};base64,${data}`}
            alt={artifact.title || t("common:image")}
            sx={{ maxWidth: "100%", maxHeight: height, objectFit: "contain" }}
          />
        );
      }
      case "text":
      default:
        return (
          <Typography variant="body2" sx={{ whiteSpace: "pre-line", p: 1 }}>
            {typeof artifact.payload === "string"
              ? artifact.payload
              : JSON.stringify(artifact.payload, null, 2)}
          </Typography>
        );
    }
  };

  return (
    <Box sx={{ width: "100%" }}>
      {artifact.title && (
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          {artifact.title}
        </Typography>
      )}
      {renderContent()}
    </Box>
  );
}

// Memoized for the same reason: an ancestor re-render must not reach Plotly
// unless the artifact or its size actually changed.
export default React.memo(ArtifactRenderer);

ArtifactRenderer.propTypes = {
  artifact: PropTypes.shape({
    type: PropTypes.string.isRequired,
    payload: PropTypes.any,
    title: PropTypes.string,
    overridden: PropTypes.bool,
  }).isRequired,
  height: PropTypes.number,
};
