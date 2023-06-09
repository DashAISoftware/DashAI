import React, { useState, useEffect } from "react";
import { Grid, Paper } from "@mui/material";
import PropTypes from "prop-types";
import Upload from "../Upload";
import { getSchema as getSchemaRequest } from "../../api/oldEndpoints";
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
  const { enqueueSnackbar } = useSnackbar();

  async function getSchema() {
    setLoading(true);
    try {
      const schema = await getSchemaRequest(
        "dataloader",
        newDataset.dataloader,
      );
      setSchema(schema);
    } catch (error) {
      enqueueSnackbar(
        "Error while trying to obtain json object for the selected dataloader",
        {
          variant: "error",
          anchorOrigin: {
            vertical: "top",
            horizontal: "right",
          },
        },
      );
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  }

  const handleFileUpload = (file, url) => {
    setNewDataset({ ...newDataset, file, url });
    // TODO: validate the dataloader form before enabling the next button
    setNextEnabled(file !== null);
  };

  // fetch json schema with the dataloader parameters
  useEffect(() => {
    getSchema();
  }, []);
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
        <Grid item xs={12} md={6}>
          <Upload onFileUpload={handleFileUpload} />
        </Grid>

        {/* Configure dataloader parameters */}
        <Grid item xs={12} md={6}>
          {!loading && (
            <DataloaderConfiguration
              dataloader={newDataset.dataloader}
              paramsSchema={schema}
              formSubmitRef={formSubmitRef}
              onSubmit={(values) =>
                setNewDataset({ ...newDataset, params: values })
              }
              newDataset={newDataset}
            />
          )}
        </Grid>
      </Grid>
    </Paper>
  );
}

ConfigureAndUploadDataset.propTypes = {
  newDataset: PropTypes.shape({
    task_name: PropTypes.string,
    dataloader: PropTypes.string,
    file: PropTypes.oneOfType([
      PropTypes.instanceOf(File),
      PropTypes.oneOf([null]),
    ]),
    url: PropTypes.string,
    params: PropTypes.objectOf(
      PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.number]),
    ),
  }).isRequired,
  setNewDataset: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
};

export default ConfigureAndUploadDataset;
