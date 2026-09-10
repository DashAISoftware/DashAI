import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box, Tooltip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

/**
 * Keys of the visualizers used to render explorer results.
 */
export const visualizersKeys = {
  tabular: "tabular",
  plotly_json: "plotly_json",
  image_base64: "image_base64",
  image_url: "image_url",
};

/**
 * NullCell component to render null values in the tabular visualizer
 */
function NullCell() {
  const [hover, setHover] = useState(false);
  const { t } = useTranslation(["common"]);
  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
      }}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <Typography variant="body2" color="text.disabled">
        {hover ? t("common:none") : "-"}
      </Typography>
    </Box>
  );
}

NullCell.propTypes = {};

const buildTableColumn = (field, headerName) => ({
  field,
  headerName,
  renderCell: (params) => {
    if (params.value === null) {
      return <NullCell />;
    } else if (typeof params.value === "object") {
      const tooltip = JSON.stringify(params.value);
      return (
        <Tooltip title={tooltip} arrow>
          <Typography variant="body2" color="text.secondary">
            {JSON.stringify(params.value)}
          </Typography>
        </Tooltip>
      );
    } else if (
      params.value !== "" &&
      !isNaN(params.value) &&
      !Number.isInteger(params.value)
    ) {
      const tooltip = params.value;
      const display = parseFloat(params.value).toFixed(2);
      return (
        <Tooltip title={tooltip} arrow>
          <Typography variant="body2">{display}</Typography>
        </Tooltip>
      );
    }
    const tooltip = params.value;
    return (
      <Tooltip title={tooltip} arrow>
        <Typography variant="body2">{params.value}</Typography>
      </Tooltip>
    );
  },
});

/**
 * Convert a typed artifact ({type, payload, title}) returned by the backend
 * into the {dataType, data} pair consumed by the explorer visualizers
 * (TabularVisualizer, PlotlyJsonVisualizer, ImageVisualizer).
 * @param {Object} artifact The artifact to convert
 * @returns {{dataType: string, data: any}}
 */
export function artifactToVisualizerData(artifact) {
  switch (artifact?.type) {
    case "plotly": {
      const figure =
        typeof artifact.payload === "string"
          ? JSON.parse(artifact.payload)
          : artifact.payload;
      return { dataType: visualizersKeys.plotly_json, data: figure };
    }
    case "table": {
      const { columns = [], rows = [] } = artifact.payload ?? {};
      const gridColumns = columns.map((column) =>
        buildTableColumn(column, column === "index" ? "Index" : column),
      );
      const gridRows = rows.map((row, rowIndex) => {
        const gridRow = { id: rowIndex };
        columns.forEach((column, columnIndex) => {
          gridRow[column] = row[columnIndex];
        });
        return gridRow;
      });
      return {
        dataType: visualizersKeys.tabular,
        data: { columns: gridColumns, rows: gridRows },
      };
    }
    case "image": {
      const { data = "", mime = "image/png" } = artifact.payload ?? {};
      return {
        dataType: visualizersKeys.image_url,
        data: `data:${mime};base64,${data}`,
      };
    }
    default:
      throw new Error(
        `No visualizer found for artifact type: ${artifact?.type}`,
      );
  }
}
