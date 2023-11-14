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
}) {
  const [loading, setLoading] = useState(true);
  const { enqueueSnackbar } = useSnackbar();
  const [rows, setRows] = useState([]);
  const typesList = [
    "Value: null",
    "Value: bool",
    "Value: int8",
    "Value: int16",
    "Value: int32",
    "Value: int64",
    "Value: uint8",
    "Value: uint16",
    "Value: uint32",
    "Value: uint64",
    "Value: float16",
    "Value: float32",
    "Value: float64",
    "Value: time32[(s|ms)]",
    "Value: time64[(us|ns)]",
    "Value: timestamp[(s|ms|us|ns)]",
    "Value: timestamp[(s|ms|us|ns), tz=(tzstring)]",
    "Value: date32",
    "Value: date64",
    "Value: duration[(s|ms|us|ns)]",
    "Value: decimal128",
    "Value: decimal256",
    "Value: binary",
    "Value: large_binary",
    "Value: string",
    "Value: large_string",
  ];

  const getDatasetSample = async () => {
    setLoading(true);
    try {
      const dataset = await getDatasetSampleRequest(uploadedDataset.id);
      const types = await getDatasetTypesRequest(uploadedDataset.id);
      const rowsArray = Object.keys(dataset).map((name) => {
        return {
          id: uuid(),
          column_name: name,
          example: dataset[name][0],
          type: types[name],
        };
      });
      setRows(rowsArray);
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
      getDatasetSample();
      setNextEnabled(true);
    }
  }, [datasetUploaded]);
  const columns = [
    {
      field: "column_name",
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
      field: "type",
      headerName: "Type",
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
};
export default DatasetSummaryStep;
