import React, { useEffect, useState } from "react";
import { useSnackbar } from "notistack";
import { Paper, Grid, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { DataGrid, useGridApiContext } from "@mui/x-data-grid";
import {
  getDatasetSample as getDatasetSampleRequest,
  getDatasetTypes as getDatasetTypesRequest,
} from "../../api/datasets";
import { dataTypesList, columnTypesList } from "../../utils/typesLists";
import SelectTypeCell from "./SelectTypeCell";
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

  const getDatasetInfo = async () => {
    setLoading(true);
    try {
      const dataset = await getDatasetSampleRequest(uploadedDataset.id);
      const types = await getDatasetTypesRequest(uploadedDataset.id);
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

  const updateCellValue = async (id, field, newValue) => {
    const apiRef = useGridApiContext();
    await apiRef.current.setEditCellValue({ id, field, value: newValue });
    apiRef.current.stopCellEditMode({ id, field });

    setRows((prevRows) =>
      prevRows.map((row) =>
        row.id === id ? { ...row, [field]: newValue } : row,
      ),
    );

    const columnName = rows.find((row) => row.id === id)?.columnName;
    const updateColumns = { ...updateColumnTypes };

    if (field === "dataType") {
      updateColumns[columnName].dtype = newValue;
    } else if (field === "columnType") {
      updateColumns[columnName].type = newValue;
    }

    setUpdateColumnTypes(updateColumns);
  };
  const renderSelectCell = (params, options) => {
    return (
      <SelectTypeCell
        id={params.id}
        value={params.value}
        field={params.field}
        options={options}
        updateValue={updateCellValue}
      />
    );
  };

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
      renderEditCell: (params) => renderSelectCell(params, columnTypesList),
      minWidth: 200,
      editable: true,
    },
    {
      field: "dataType",
      headerName: "Data type",
      renderEditCell: (params) => renderSelectCell(params, dataTypesList),
      minWidth: 200,
      editable: true,
    },
  ];
  useEffect(() => {
    if (datasetUploaded) {
      getDatasetInfo();
      setNextEnabled(true);
    }
  }, [datasetUploaded]);

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
