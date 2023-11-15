import React, { useEffect, useState } from "react";
import { useSnackbar } from "notistack";
import { Paper, Grid, Typography, Select } from "@mui/material";
import PropTypes from "prop-types";
import { DataGrid, useGridApiContext } from "@mui/x-data-grid";
import uuid from "react-uuid";
import {
  getDatasetSample as getDatasetSampleRequest,
  getDatasetTypes as getDatasetTypesRequest,
} from "../../api/datasets";
function DatasetSummaryStep({
  uploadedDataset,
  setNextEnabled,
  datasetUploaded,
  updateColumnTypes,
  setUpdateColumnTypes,
}) {
  const [loading, setLoading] = useState(true);
  const { enqueueSnackbar } = useSnackbar();
  const [rows, setRows] = useState([]);
  const typesList = [
    "null",
    "bool",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "float16",
    "float32",
    "float64",
    "time32[(s|ms)]",
    "time64[(us|ns)]",
    "timestamp[(s|ms|us|ns)]",
    "timestamp[(s|ms|us|ns), tz=(tzstring)]",
    "date32",
    "date64",
    "duration[(s|ms|us|ns)]",
    "decimal128",
    "decimal256",
    "binary",
    "large_binary",
    "string",
    "large_string",
  ];

  const getDatasetInfo = async () => {
    setLoading(true);
    try {
      const dataset = await getDatasetSampleRequest(uploadedDataset.id);
      const types = await getDatasetTypesRequest(uploadedDataset.id);
      const rowsArray = Object.keys(dataset).map((name) => {
        return {
          id: uuid(),
          columnName: name,
          example: dataset[name][0],
          columnType: types[name].type,
          dataType: types[name].dtype,
        };
      });
      setRows(rowsArray);
      setUpdateColumnTypes(types);
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

  function SelectEditInputCell(props) {
    const { id, value, field } = props;
    const apiRef = useGridApiContext();

    const handleChange = async (event) => {
      const selectedValue = event.target.value;
      await apiRef.current.setEditCellValue({
        id,
        field,
        value: event.target.value,
      });
      apiRef.current.stopCellEditMode({ id, field });

      // Update rows with the new value
      setRows((prevRows) =>
        prevRows.map((row) =>
          row.id === id ? { ...row, [field]: selectedValue } : row,
        ),
      );
      const columnName = rows.find((row) => row.id === id)?.columnName;
      const updateColumns = { ...updateColumnTypes };
      updateColumns[columnName].dtype = selectedValue;
      setUpdateColumnTypes(updateColumns);
    };
    return (
      <Select
        native
        value={value || ""}
        onChange={handleChange}
        size="small"
        sx={{ height: 1 }}
        autoFocus
      >
        {typesList.map((type) => (
          <option key={type} value={type}>
            {type}
          </option>
        ))}
      </Select>
    );
  }
  SelectEditInputCell.propTypes = {
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    value: PropTypes.string.isRequired,
    field: PropTypes.string.isRequired,
  };
  const renderSelectEditInputCell = (params) => {
    return <SelectEditInputCell {...params} />;
  };

  useEffect(() => {
    if (datasetUploaded) {
      getDatasetInfo();
      setNextEnabled(true);
    }
  }, [datasetUploaded]);
  const columns = [
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
      minWidth: 200,
      editable: false,
    },
    {
      field: "dataType",
      headerName: "Data type",
      renderEditCell: renderSelectEditInputCell,
      minWidth: 350,
      editable: true,
    },
  ];
  return (
    <Paper
      variant="outlined"
      sx={{ p: 4, maxHeight: "55vh", overflow: "auto" }}
    >
      <Grid container direction={"column"} alignItems={"center"}>
        <Grid item>
          <Typography variant="subtitle1">Dataset Summary</Typography>
          <Typography
            item
            variant="caption"
            component="h3"
            sx={{ mb: 2, color: "grey" }}
          >
            Summary of the recently uploaded dataset with predefined column
            types. You can modify the type by selecting a different value.
          </Typography>
        </Grid>
        <Grid item>
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
        </Grid>
      </Grid>
    </Paper>
  );
}
DatasetSummaryStep.propTypes = {
  uploadedDataset: PropTypes.object,
  setNextEnabled: PropTypes.func.isRequired,
  datasetUploaded: PropTypes.bool,
  updateColumnTypes: PropTypes.object.isRequired,
  setUpdateColumnTypes: PropTypes.func.isRequired,
};
export default DatasetSummaryStep;
