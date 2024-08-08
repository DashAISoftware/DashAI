import React, { useCallback } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Grid } from "@mui/material";
import DeleteItemModal from "../custom/DeleteItemModal";
import { parseIndexToRange } from "../../utils/parseRange";
import PropTypes from "prop-types";

const ConverterTable = ({
  appliedConvertersList,
  updateAppliedConvertersList,
}) => {
  const createDeleteHandler = useCallback(
    (id) => () => {
      const newSelectedConverters = appliedConvertersList
        .filter((converter) => converter.id !== id)
        .map((converter, index) => ({
          ...converter,
          order: index + 1, // Update order
        }));
      updateAppliedConvertersList(newSelectedConverters);
    },
    [appliedConvertersList],
  );

  const columns = React.useMemo(
    () => [
      {
        field: "order",
        headerName: "Order",
        minWidth: 50,
        editable: false,
        sortable: true,
      },
      {
        field: "name",
        headerName: "Converter",
        minWidth: 250,
        editable: false,
        sortable: false,
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 150,
        getActions: (params) => [
          <DeleteItemModal
            key="delete-component"
            deleteFromTable={createDeleteHandler(params.id)}
          />,
        ],
      },
    ],
    [createDeleteHandler],
  );

  return (
    <Grid container>
      {/* Selected converters table */}
      <Grid item xs={12}>
        <DataGrid
          rows={appliedConvertersList}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: {
                pageSize: 5,
              },
            },
          }}
          pageSize={5}
          pageSizeOptions={[5, 10]}
          disableRowSelectionOnClick
          autoHeight
          loading={false}
        />
      </Grid>
    </Grid>
  );
};

ConverterTable.propTypes = {
  appliedConvertersList: PropTypes.arrayOf(PropTypes.object),
  updateAppliedConvertersList: PropTypes.func,
};

ConverterTable.defaultProps = {
  appliedConvertersList: [],
  updateAppliedConvertersList: () => {},
};

export default ConverterTable;