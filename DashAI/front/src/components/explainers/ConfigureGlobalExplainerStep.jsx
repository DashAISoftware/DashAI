import React, { useState, useEffect } from "react";
import { Grid, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

import { getSchema as getSchemaRequest } from "../../api/oldEndpoints";
import ExplainerConfiguration from "./ExplainerConfiguration";

function ConfigureExplainerStep({ newExpl, setNewExpl, setNextEnabled }) {
  const [schema, setSchema] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  console.log(schema);

  const getSchema = async () => {
    setLoading(true);
    try {
      const schema = await getSchemaRequest(
        "explainer",
        newExpl.explainer_name,
      );
      console.log("schema");
      console.log(schema);
      setSchema(schema);
    } catch (error) {
      setError(true);
      enqueueSnackbar(
        "Error while trying to obtain json object for the selected explainer",
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
  };

  useEffect(() => {
    getSchema();
  }, []);

  return (
    <Grid
      container
      direction="row"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={3}
    >
      <Grid item xs={12}>
        <Typography variant="h5" component="h3">
          Configure your Explainer
        </Typography>
      </Grid>
      {/* Configure dataloader parameters */}
      <Grid item xs={12} md={6}>
        {!loading && !error && (
          <ExplainerConfiguration paramsSchema={schema} explainer={newExpl} />
        )}
      </Grid>
    </Grid>
  );
}

ConfigureExplainerStep.propTypes = {
  newExpl: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    explainer_name: PropTypes.string,
  }),
  setNewExpl: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default ConfigureExplainerStep;
