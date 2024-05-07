import React, { useState, useEffect } from "react";
import { Grid, Paper } from "@mui/material";
import PropTypes from "prop-types";
import Upload from "./Upload";
import { getComponents as getComponentsRequest } from "../../api/component";
import { useSnackbar } from "notistack";
import DataloaderConfiguration from "./DataloaderConfiguration";

/**
 * This component combines in a single step the process of uploading a file and configuring the dataloader parameters.
 * @param {object} newDataset An object that stores all the important states for the dataset modal.
 * @param {function} setNewDataset function that modifies newDataset state
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the modal.
 * @param {object} formSubmitRef useRef to trigger form submit from outside "ParameterForm" component
 */
function ConfigureAndUploadDataset({
  newDataset,
  setNewDataset,
  setNextEnabled,
  formSubmitRef,
}) {
  const [schema, setSchema] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  async function getSchema() {
    setLoading(true);
    try {
      const schema = await getComponentsRequest({
        model: newDataset.dataloader,
      });

      setSchema(schema);
    } catch (error) {
      setError(true);
      enqueueSnackbar(
        "Error while trying to obtain json object for the selected dataloader",
      );
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
  }

  const handleFileUpload = (file, url) => {
    setNewDataset({ ...newDataset, file, url });
  };

  // fetch json schema with the dataloader parameters
  useEffect(() => {
    getSchema();
  }, []);

  useEffect(() => {
    if (newDataset.file !== null && !error) {
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [error, newDataset.file]);

  return (
    <Paper variant="outlined" sx={{ p: 4 }}>
      <Grid
        container
        direction="row"
        justifyContent="space-around"
        alignItems="stretch"
        spacing={3}
      >
        {/* Upload file */}
        <Grid item xs={12} md={5}>
          <Upload onFileUpload={handleFileUpload} />
        </Grid>

        {/* Configure dataloader parameters */}
        <Grid item xs={12} md={7}>
          {!loading && Object.keys(schema).length > 0 && (
            <DataloaderConfiguration
              dataloader={newDataset.dataloader}
              paramsSchema={schema}
              formSubmitRef={formSubmitRef}
              onSubmit={(values) => {
                setNewDataset({ ...newDataset, params: values });
              }}
              newDataset={newDataset}
              setError={setError}
              error={error}
            />
          )}
        </Grid>
      </Grid>
    </Paper>
  );
}

ConfigureAndUploadDataset.propTypes = {
  newDataset: PropTypes.shape({
    dataloader: PropTypes.string,
    file: PropTypes.oneOfType([
      PropTypes.instanceOf(File),
      PropTypes.oneOf([null]),
    ]),
    url: PropTypes.string,
    params: PropTypes.shape({}),
  }).isRequired,
  setNewDataset: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
};

export default ConfigureAndUploadDataset;
