import React, { useEffect, useState } from "react";
import { useSnackbar } from "notistack";
import { Paper, Grid, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { DataGrid } from "@mui/x-data-grid";
import uuid from "react-uuid";
import {
  getDatasetSample as getDatasetSampleRequest,
  getDatasetTypes as getDatasetTypesRequest,
} from "../../api/datasets";
function DatasetPreviewStep({
  uploadedDataset,
  setNextEnabled,
  datasetUploaded,
}) {
  const [loading, setLoading] = useState(true);
  const { enqueueSnackbar } = useSnackbar();
  const [rows, setRows] = useState([]);

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
      minWidth: 200,
      editable: false,
    },
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

  useEffect(() => {
    if (datasetUploaded) {
      getDatasetSample();
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
        </Grid>
      </Grid>
    </Paper>
  );
}
DatasetPreviewStep.propTypes = {
  uploadedDataset: PropTypes.object,
  setNextEnabled: PropTypes.func.isRequired,
  datasetUploaded: PropTypes.bool,
};
export default DatasetPreviewStep;
