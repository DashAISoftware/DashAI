import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import { Box, CircularProgress, Tooltip, Typography } from "@mui/material";

import { useExplorerContext } from "../context";
import { getExplorerResults } from "../../../api/explorer";
import { TabularVisualizer } from "../Visualizations";

function NullCell({}) {
  const [hover, setHover] = useState(false);
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
        {hover ? "None" : "-"}
      </Typography>
    </Box>
  );
}

const visualizers = {
  tabular: TabularVisualizer,
};

const ORIENTATIONS = {
  dict: "dict",
  records: "records",
};

const getDataFromOrientation = (data, orientation) => {
  let res = {
    columns: [],
    rows: [],
  };

  if (orientation === ORIENTATIONS.records) {
    throw new Error(`orientation ${orientation} not supported`);
  }

  if (orientation === ORIENTATIONS.dict) {
    // ‘dict’ (default) : dict like {column -> {index -> value}}
    // Get the columns
    const columns = Object.keys(data);
    res.columns = [
      {
        field: "id",
        headerName: "Index",
        width: 150,
      },
      ...columns.map((column) => {
        return {
          field: column,
          headerName: column,
          width: 150,
          renderCell: (params) => {
            if (params.value === null) {
              return <NullCell />;
            } else if (typeof params.value === "object") {
              return (
                <Typography variant="body2" color="text.secondary">
                  {JSON.stringify(params.value)}
                </Typography>
              );
            } else if (
              params.value !== "" &&
              !isNaN(params.value) &&
              !Number.isInteger(params.value)
            ) {
              const tooltip = params.value;
              const display = parseFloat(params.value).toFixed(2);
              return (
                <Tooltip title={tooltip}>
                  <Typography variant="body2">{display}</Typography>
                </Tooltip>
              );
            }
            return <Typography variant="body2">{params.value}</Typography>;
          },
        };
      }),
    ];

    // Get the rows
    const rows = [];
    const indexes = Object.keys(data[columns[0]]);
    indexes.forEach((index) => {
      const row = {
        id: index,
      };
      columns.forEach((column) => {
        row[column] = data[column][index];
      });
      rows.push(row);
    });
    res.rows = rows;
  }

  return res;
};

function StepVisualize({}) {
  const { explorerData } = useExplorerContext();
  const { explorerId } = explorerData;

  const [loading, setLoading] = useState(false);
  const [dataType, setDataType] = useState(null);
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);

  const fetchExplorerResults = async () => {
    setLoading(true);
    getExplorerResults(explorerId)
      .then((results) => {
        if (!results?.type) {
          throw new Error("No result type specified in the response");
        }

        // Check if there is an appropriate visualizer
        if (!Object.keys(visualizers).includes(results.type)) {
          throw new Error(`No visualizer found for type: ${results.type}`);
        }
        setDataType(results.type);

        // Get the data from the orientation
        const data = getDataFromOrientation(results.data, results.orient);
        setColumns(data.columns);
        setRows(data.rows);
      })
      .catch((error) => {
        console.error(error);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    // Fetch the results data
    if (explorerId) {
      fetchExplorerResults();
    }
  }, [explorerId]);

  return (
    <Box
      sx={{
        height: "100%",
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {loading && <CircularProgress />}

      {!loading && dataType && (
        <TabularVisualizer loading={loading} columns={columns} rows={rows} />
      )}
    </Box>
  );
}

StepVisualize.propTypes = {};

export default StepVisualize;
