import PropTypes from "prop-types";
import React from "react";

import { DataGrid } from "@mui/x-data-grid";

import useExperimentsTable from "../hooks/useExperimentsTable";
import ExperimentsTableLayout from "./ExperimentsTableLayout";
import ExperimentsTableToolbar from "./ExperimentsTableToolbar";

function ExperimentsTable({
  handleOpenNewExperimentModal,
  updateTableFlag,
  setUpdateTableFlag,
}) {
  const { rows, columns, loading } = useExperimentsTable({
    updateTableFlag,
    setUpdateTableFlag,
  });
  return (
    <ExperimentsTableLayout
      toolbar={
        <ExperimentsTableToolbar
          handleOpenNewExperimentModal={handleOpenNewExperimentModal}
          handleUpdateExperiments={() => setUpdateTableFlag(true)}
        />
      }
    >
      <DataGrid
        rows={rows}
        columns={columns}
        initialState={{
          pagination: {
            paginationModel: {
              pageSize: 5,
            },
          },
        }}
        sortModel={[{ field: "id", sort: "desc" }]}
        columnVisibilityModel={{ id: false }}
        pageSizeOptions={[5, 10]}
        disableRowSelectionOnClick
        autoHeight
        loading={loading}
      />
    </ExperimentsTableLayout>
  );
}

ExperimentsTable.propTypes = {
  handleOpenNewExperimentModal: PropTypes.func,
  updateTableFlag: PropTypes.bool.isRequired,
  setUpdateTableFlag: PropTypes.func.isRequired,
};

export default ExperimentsTable;
