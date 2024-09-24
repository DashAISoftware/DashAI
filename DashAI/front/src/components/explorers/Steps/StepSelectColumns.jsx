import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";

import { Box } from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { useSnackbar } from "notistack";

import { getDatasetTypes } from "../../../api/datasets";
import { useExplorerContext } from "../context";

const gridColumns = [
  {
    field: "columnName",
    headerName: "Column Name",
    width: 200,
  },
  {
    field: "dataType",
    headerName: "Data Type",
    width: 200,
  },
];

function StepSelectColumns({ disableChanges = false }) {
  const { explorerData, setSelectedColumns } = useExplorerContext();
  const { datasetId, selectedColumns } = explorerData;
  const { enqueueSnackbar } = useSnackbar();

  const [loading, setLoading] = useState(false);
  const [columns, setColumns] = useState([]);
  const [rowSelectionModel, setRowSelectionModel] = useState([]);

  const loadDatasetTypes = async () => {
    setLoading(true);
    getDatasetTypes(datasetId)
      .then((data) => {
        let cols = Object.keys(data).map((name, idx) => {
          return {
            id: idx,
            columnName: name,
            dataType: data[name].dtype,
          };
        });
        // update columns and row selection model
        setColumns(cols);
        setRowSelectionModel(selectedColumns.map((col) => col.id));
      })
      .catch((err) => {
        console.error(err);
        enqueueSnackbar("Failed to load dataset types.");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // load dataset types on mount
  useEffect(() => {
    loadDatasetTypes();
  }, []);

  const handleSelection = (selection) => {
    if (disableChanges) return;
    setRowSelectionModel(selection);
    setSelectedColumns(columns.filter((col) => selection.includes(col.id)));
  };

  return (
    <Box sx={{ height: "100%", width: "100%" }}>
      <DataGrid
        autoHeight
        loading={loading}
        rows={columns}
        columns={gridColumns}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
        }}
        pageSize={5}
        pageSizeOptions={[5, 10, 20]}
        checkboxSelection
        onRowSelectionModelChange={handleSelection}
        rowSelectionModel={rowSelectionModel}
      />
    </Box>
  );
}

StepSelectColumns.propTypes = {
  disableChanges: PropTypes.bool,
};

export default StepSelectColumns;
