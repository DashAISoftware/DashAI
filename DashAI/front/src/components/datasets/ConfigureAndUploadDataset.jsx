import React, { useState, useEffect } from "react";
import { Grid, Paper } from "@mui/material";
import PropTypes from "prop-types";
import Upload from "../Upload";
import { getSchema as getSchemaRequest } from "../../api/oldEndpoints";
import { useSnackbar } from "notistack";
import ParamsModal from "../ConfigurableObject/ParamsModal";

function ConfigureAndUploadDataset({
  newDataset,
  setNewDataset,
  setNextEnabled,
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

  // fetch json schema to configure dataloader
  useEffect(() => {
    getSchema();
  }, []);

  const onFileUpload = (file, url) => {
    setNewDataset({ ...newDataset, file, url });
    // TODO: validate the form before enabling the next button
    setNextEnabled(true);
  };
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
          <Upload onFileUpload={onFileUpload} />
        </Grid>

        {/* Configure parameters */}
        <Grid item xs={12} md={6}>
          {!loading && (
            <ParamsModal
              dataloader={newDataset.dataloader}
              paramsSchema={schema}
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
  }).isRequired,
  setNewDataset: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default ConfigureAndUploadDataset;
