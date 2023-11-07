import React, { useEffect, useState } from "react";
import { useSnackbar } from "notistack";
import { Paper, Grid, Typography } from "@mui/material";
import ParameterForm from "../ConfigurableObject/ParameterForm";
import PropTypes from "prop-types";
import { DataGrid } from "@mui/x-data-grid";
import uuid from "react-uuid";
import { getDatasetSample as getDatasetSampleRequest } from "../../api/datasets";
function DatasetPreview({ datasetId, datasetUploaded }) {
  const [loading, setLoading] = useState(true);
  const { enqueueSnackbar } = useSnackbar();
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);

  const getDatasetSample = async () => {
    setLoading(true);
    try {
      const dataset = await getDatasetSampleRequest(datasetId);
      const columnHeaders = Object.keys(dataset);
      const columns = columnHeaders.map((header) => {
        return {
          field: header,
          headerName: header,
          minWidth: 50,
          editable: false,
        };
      });
      const rowsArray = dataset[columnHeaders[0]].map((_, index) => {
        const obj = { id: uuid() };
        columnHeaders.forEach((header) => {
          obj[header] = dataset[header][index];
        });
        return obj;
      });
      setColumns(columns);
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

  useEffect(() => {
    if (datasetUploaded) {
      getDatasetSample();
    }
  }, [datasetUploaded]);

  return (
    <Paper
      variant="outlined"
      sx={{ p: 4, maxHeight: "55vh", overflow: "auto" }}
    >
      <Grid container direction={"column"} alignItems={"center"}>
        <Grid item>
          <Typography variant="subtitle1">Dataset Preview</Typography>
        </Grid>
        <Grid item>
          <DataGrid
            rows={rows}
            columns={columns}
            pageSize={10}
            loading={loading}
            autoHeight
          />
        </Grid>
        <Grid item>
          <Typography variant="subtitle1">Configuration Parameters</Typography>
          <ParameterForm />
        </Grid>
      </Grid>
    </Paper>
  );
}
DatasetPreview.propTypes = {
  datasetId: PropTypes.number,
  datasetUploaded: PropTypes.bool,
};
export default DatasetPreview;
