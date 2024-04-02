import React from "react";
import PropTypes from "prop-types";
import { Paper, Alert, AlertTitle, CircularProgress } from "@mui/material";
import { DataGrid, GridToolbar } from "@mui/x-data-grid";
import ResultsDetails from "./ResultsDetails";

function ResultsTableLayout({ experimentId, rows, columns, showRunResults,
                              loading, selectedRunId, handleCloseRunResults,
                              columnVisibilityModel, columnGroupingModel }) {
  return (
    <Paper
      sx={{
        p: 4,
      }}
    >
      {experimentId === undefined && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          <AlertTitle>No experiment selected</AlertTitle>
          Select an experiment to see the runs associated to it
        </Alert>
      )}
      {!loading ? (
        <DataGrid
          rows={rows}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: 10,
              },
            },
            columns: {
              columnVisibilityModel,
            },
          }}
          experimentalFeatures={{ columnGrouping: true }}
          columnGroupingModel={columnGroupingModel}
          slots={{
            toolbar: GridToolbar,
          }}
          pageSizeOptions={[10]}
          density="compact"
          disableRowSelectionOnClick
          autoHeight
          sx={{
            ".MuiDataGrid-cell:focus": {
              outline: "none",
            },
            "& .MuiDataGrid-row:hover": {},
          }}
        />
      ) : (
        <CircularProgress color="inherit" />
      )}

      {showRunResults && (
        <ResultsDetails
          runId={selectedRunId}
          onClose={handleCloseRunResults}
          key={selectedRunId}
        />
      )}
    </Paper>
  );
}

ResultsTableLayout.propTypes = {
  experimentId: PropTypes.string,
  rows: PropTypes.array,
  columns: PropTypes.array,
  showRunResults: PropTypes.bool,
  selectedRunId: PropTypes.number,
  handleCloseRunResults: PropTypes.func,
  columnVisibilityModel: PropTypes.objectOf(PropTypes.bool),
  columnGroupingModel:PropTypes.array,
};

export default ResultsTableLayout;
