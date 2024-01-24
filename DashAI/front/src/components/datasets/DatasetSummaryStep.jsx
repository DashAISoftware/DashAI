import React, { useEffect } from "react";
import { Paper, Grid, Typography, CircularProgress } from "@mui/material";
import PropTypes from "prop-types";
import DatasetSummaryTable from "./DatasetSummaryTable";
function DatasetSummaryStep({
  uploadedDataset,
  setNextEnabled,
  datasetUploaded,
  columnsSpec,
  setColumnsSpec,
}) {
  useEffect(() => {
    if (datasetUploaded) {
      setNextEnabled(true);
    }
  }, []);
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
          {datasetUploaded ? (
            <DatasetSummaryTable
              datasetId={uploadedDataset.id}
              isEditable={true}
              columnsSpec={columnsSpec}
              setColumnsSpec={setColumnsSpec}
            />
          ) : (
            <CircularProgress />
          )}
        </Grid>
      </Grid>
    </Paper>
  );
}
DatasetSummaryStep.propTypes = {
  uploadedDataset: PropTypes.object,
  setNextEnabled: PropTypes.func.isRequired,
  datasetUploaded: PropTypes.bool,
  columnsSpec: PropTypes.object.isRequired,
  setColumnsSpec: PropTypes.func.isRequired,
};
export default DatasetSummaryStep;
