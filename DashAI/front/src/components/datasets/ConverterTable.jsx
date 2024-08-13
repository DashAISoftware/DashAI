import React, { useCallback, useState, useEffect } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Grid } from "@mui/material";
import DeleteItemModal from "../custom/DeleteItemModal";
import ConverterEditorModal from "./ConverterEditorModal";
import PropTypes from "prop-types";
import ConverterScopeModal from "./ConverterScopeModal";
import { getDatasetInfo as getDatasetInfoRequest } from "../../api/datasets";
import { parseIndexToRange } from "../../utils/parseRange";

const ConverterTable = ({
  datasetId,
  convertersToApply,
  setConvertersToApply,
}) => {
  const [datasetInfo, setDatasetInfo] = useState({});
  const [loading, setLoading] = useState(true);

  const getDatasetInfo = async () => {
    setLoading(true);
    try {
      const datasetInfo = await getDatasetInfoRequest(datasetId);
      setDatasetInfo({ ...datasetInfo, id: datasetId });
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the dataset info.");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getDatasetInfo();
  }, []);

  const createDeleteHandler = useCallback(
    (id) => () => {
      const newSelectedConverters = convertersToApply
        .filter((converter) => converter.id !== id)
        .map((converter, index) => ({
          ...converter,
          order: index + 1, // Update order
        }));
      setConvertersToApply(newSelectedConverters);
    },
    [convertersToApply],
  );

  const handleUpdateConverter = (id, key) => (newValues) => {
    const updatedConverters = convertersToApply.map((converter) =>
      converter.id === id ? {
        ...converter,
        [key]: newValues,
      } : converter,
    );
    setConvertersToApply(updatedConverters);
  };

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
        field: `columns`,
        headerName: "Columns",
        minWidth: 100,
        editable: false,
        sortable: false,
        valueGetter: (params) => params.row.scope.columns,
        valueFormatter: (params) => {
          const columns = params.value ?? [];
          return columns.length > 0
            ? parseIndexToRange(columns).join(", ")
            : "All columns";
        },
      },
      {
        field: `rows`,
        headerName: "Rows",
        minWidth: 100,
        editable: false,
        sortable: false,
        valueGetter: (params) => params.row.scope.rows,
        valueFormatter: (params) => {
          const rows = params.value ?? [];
          return rows.length > 0
            ? parseIndexToRange(rows).join(", ")
            : "All rows";
        },
      },
      {
        field: "actions",
        type: "actions",
        minWidth: 150,
        getActions: (params) => [
          <ConverterScopeModal
            key="scope-component"
            converterToConfigure={params.row.name}
            updateScope={handleUpdateConverter(params.row.id, "scope")}
            scopeInitialValues={params.row.scope}
            datasetInfo={datasetInfo}
          />,
          <ConverterEditorModal
            key="edit-component"
            converterToConfigure={params.row.name}
            updateParameters={handleUpdateConverter(params.row.id, "params")}
            paramsInitialValues={params.row.params}
          />,
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
          rows={convertersToApply}
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
          loading={loading}
        />
      </Grid>
    </Grid>
  );
};

ConverterTable.propTypes = {
  convertersToApply: PropTypes.arrayOf(PropTypes.object),
  setConvertersToApply: PropTypes.func,
};

ConverterTable.defaultProps = {
  convertersToApply: [],
  setConvertersToApply: () => {},
};

export default ConverterTable;
