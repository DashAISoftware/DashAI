import React from "react";
import PropTypes from "prop-types";

import { DataGrid, GridToolbar } from "@mui/x-data-grid";

function TabularVisualizer({
  loading = false,
  rows = [],
  columns = [],
  ...props
}) {
  return (
    <DataGrid
      loading={loading}
      rows={rows}
      columns={columns}
      autoPageSize
      disableRowSelectionOnClick
      slots={{
        toolbar: GridToolbar,
      }}
      {...props}
    />
  );
}

TabularVisualizer.propTypes = {
  loading: PropTypes.bool,
  rows: PropTypes.array,
  columns: PropTypes.array,
};

export default TabularVisualizer;
