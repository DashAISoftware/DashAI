import React, { useState, useEffect } from "react";
import { DialogContentText, Grid, Paper, Typography } from "@mui/material";
import PropTypes from "prop-types";

import FormSchema from "../shared/FormSchema";
import FormSchemaLayout from "../shared/FormSchemaLayout";
import useSchema from "../../hooks/useSchema";

function ConfigureExplainerFitStep({
  newExpl,
  setNewExpl,
  setNextEnabled,
  formSubmitRef,
}) {
  const { defaultValues } = useSchema({
    modelName: `Fit${newExpl.explainer_name}`,
  });

  const isParamsEmpty =
    !newExpl.fit_parameters || Object.keys(newExpl.fit_parameters).length === 0;

  useEffect(() => {
    if (isParamsEmpty && Boolean(defaultValues)) {
      setNewExpl({ ...newExpl, fit_parameters: defaultValues });
    }
  }, [isParamsEmpty, defaultValues]);

  const handleUpdateParameters = (values) => {
    setNewExpl((_) => ({ ...newExpl, fit_parameters: values }));
  };

  useEffect(() => {
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
              <FormSchemaLayout>
                <FormSchema
                  autoSave
                  model={`Fit${newExpl.explainer_name}`}
                  onFormSubmit={(values) => {
                    handleUpdateParameters(values);
                  }}
                  formSubmitRef={formSubmitRef}
                />
              </FormSchemaLayout>
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}

ConfigureExplainerFitStep.propTypes = {
  newExpl: PropTypes.shape({
    name: PropTypes.string,
    explainer_name: PropTypes.string,
    dataset_id: PropTypes.number,
    parameters: PropTypes.object,
    fit_parameters: PropTypes.object,
  }),
  setNewExpl: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
};

export default ConfigureExplainerFitStep;
