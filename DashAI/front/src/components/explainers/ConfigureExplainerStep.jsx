import React, { useState, useEffect } from "react";
import { DialogContentText, Grid, Paper, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

import { getSchema as getSchemaRequest } from "../../api/oldEndpoints";
import ParameterForm from "../configurableObject/ParameterForm";

function ConfigureExplainerStep({
  newExpl,
  setNewExpl,
  setNextEnabled,
  formSubmitRef,
}) {
  const [schema, setSchema] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const getSchema = async () => {
    setLoading(true);
    try {
      const schema = await getSchemaRequest(
        "global_explainer",
        newExpl.explainer_name,
      );
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

  const handleUpdateParameters = (values) => {
    console.log(newExpl);
    setNewExpl((_) => ({ ...newExpl, parameters: values }));
  };

  useEffect(() => {
    getSchema();
    setNextEnabled(true);
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
          <Paper
            variant="outlined"
            sx={{ p: 4, maxHeight: "55vh", overflow: "auto" }}
          >
            <Grid container direction={"column"} alignItems={"center"}>
              {/* Form title */}
              <Grid item>
                <DialogContentText>Explainer configuration</DialogContentText>
              </Grid>
              <Grid item sx={{ p: 3 }}>
                {/* Main dataloader form */}
                <ParameterForm
                  parameterSchema={schema}
                  onFormSubmit={handleUpdateParameters}
                  formSubmitRef={formSubmitRef}
                />
              </Grid>
            </Grid>
          </Paper>
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
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
};

export default ConfigureExplainerStep;
