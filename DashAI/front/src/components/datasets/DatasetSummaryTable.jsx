// DatasetSummaryTable.js
import React, { useEffect, useMemo, useState } from "react";
import { useSnackbar } from "notistack";
import PropTypes from "prop-types";
import { DataGrid, useGridApiContext } from "@mui/x-data-grid";
import {
  getDatasetSample as getDatasetSampleRequest,
  getDatasetTypes as getDatasetTypesRequest,
} from "../../api/datasets";
import { dataTypesList, columnTypesList } from "../../utils/typesLists";
import SelectTypeCell from "../custom/SelectTypeCell";

function DatasetSummaryTable({
  datasetId,
  isEditable,
  columnsSpec,
  setColumnsSpec,
}) {
  const [loading, setLoading] = useState(true);
  const { enqueueSnackbar } = useSnackbar();
  const [rows, setRows] = useState([]);

  const getDatasetInfo = async () => {
    setLoading(true);
    try {
      const dataset = await getDatasetSampleRequest(datasetId);
      const types = await getDatasetTypesRequest(datasetId);
      const rowsArray = Object.keys(dataset).map((name, idx) => {
        return {
          id: idx,
          columnName: name,
          example: dataset[name][0],
          columnType: types[name].type,
          dataType: types[name].dtype,
        };
      });
      setRows(rowsArray);
      if (isEditable) {
        setColumnsSpec(types);
      }
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the dataset.");
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

  const updateCellValue = async (id, field, newValue, apiRef) => {
    await apiRef.current.setEditCellValue({ id, field, value: newValue });
    apiRef.current.stopCellEditMode({ id, field });
    setRows((prevRows) =>
      prevRows.map((row) =>
        row.id === id ? { ...row, [field]: newValue } : row,
      ),
    );

    const columnName = rows.find((row) => row.id === id)?.columnName;
    const updateColumns = { ...columnsSpec };

    if (field === "dataType") {
      updateColumns[columnName].dtype = newValue;
    } else if (field === "columnType") {
      updateColumns[columnName].type = newValue;
    }

    setColumnsSpec(updateColumns);
    console.log(columnsSpec);
  };

  const renderSelectCell = (params, options) => {
    const apiRef = useGridApiContext();
    return (
      <SelectTypeCell
        id={params.id}
        value={params.value}
        field={params.field}
        options={options}
        updateValue={(id, field, newValue) =>
          updateCellValue(id, field, newValue, apiRef)
        }
      />
    );
  };

  const columns = useMemo(() => [
    {
      field: "columnName",
      headerName: "Column name",
      minWidth: 200,
      editable: false,
    },
    {
      field: "example",
      headerName: "Example",
      minWidth: 200,
      editable: false,
    },
    {
      field: "columnType",
      headerName: "Column type",
      renderEditCell: (params) =>
        isEditable && renderSelectCell(params, columnTypesList),
      minWidth: 200,
      editable: isEditable,
    },
    {
      field: "dataType",
      headerName: "Data type",
      renderEditCell: (params) =>
        isEditable && renderSelectCell(params, dataTypesList),
      minWidth: 200,
      editable: isEditable,
    },
  ]);

  useEffect(() => {
    getDatasetInfo();
  }, []);

  return (
    <DataGrid
      rows={rows}
      columns={columns}
      initialState={{
        pagination: {
          paginationModel: {
            pageSize: 4,
          },
        },
      }}
      pageSize={4}
      pageSizeOptions={[4, 5, 10]}
      loading={loading}
      autoHeight
    />
  );
}

DatasetSummaryTable.propTypes = {
  datasetId: PropTypes.number,
  isEditable: PropTypes.bool,
  columnsSpec: PropTypes.object,
  setColumnsSpec: PropTypes.func,
};

export default DatasetSummaryTable;
