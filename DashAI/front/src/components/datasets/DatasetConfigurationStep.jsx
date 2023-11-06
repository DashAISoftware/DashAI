import React from "react";
import PropTypes from "prop-types";
import DatasetPreview from "./DatasetPreview";
import SelectColumnsTypes from "./SelectColumnsTypes";
import { Grid, Paper } from "@mui/material";
// import { getDatasetTypes as getDatasetTypesRequest} from "../../api/datasets";
function DatasetConfigurationStep({
  newDataset,
  setNewDataset,
  setNextEnabled,
  datasetUploaded,
}) {
  return (
    <Paper variant="outlined" sx={{ p: 4 }}>
      {datasetUploaded && (
        <Grid
          container
          direction="row"
          justifyContent="space-around"
          alignItems="stretch"
          spacing={3}
        >
          {/*  */}

          <Grid item xs={12} md={6}>
            <DatasetPreview
              newDataset={newDataset}
              datasetUploaded={datasetUploaded}
            />
          </Grid>

          {/*  */}
          <Grid item xs={12} md={6}>
            <SelectColumnsTypes newDataset={true} />
          </Grid>
        </Grid>
      )}
    </Paper>
  );
}
DatasetConfigurationStep.propTypes = {
  newDataset: PropTypes.shape({
    dataloader: PropTypes.string,
    file: PropTypes.oneOfType([
      PropTypes.instanceOf(File),
      PropTypes.oneOf([null]),
    ]),
    url: PropTypes.string,
    params: PropTypes.object,
  }).isRequired,
  setNewDataset: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  datasetUploaded: PropTypes.bool,
};

export default DatasetConfigurationStep;
