import React, { useState, useEffect } from "react";
import { DialogContentText, Grid, Paper, Typography } from "@mui/material";
import PropTypes from "prop-types";

import FormSchema from "../shared/FormSchema";
import FormSchemaLayout from "../shared/FormSchemaLayout";
import useSchema from "../../hooks/useSchema";

function ConfigureExplainerStep({
  newExpl,
  setNewExpl,
  setNextEnabled,
  scope,
  formSubmitRef,
}) {
  const [explainerProperties, setExplainerProperties] = useState([]);
  const [explainerFitProperties, setExplainerFitProperties] = useState([]);

  const renderFitForm = scope === "Local";
  const { defaultValues } = useSchema({ modelName: newExpl.explainer_name });

  useEffect(() => {
    console.log("use effect");
    console.log(!newExpl.parameters);
    if (!newExpl.parameters && Boolean(defaultValues)) {
      setNewExpl({ ...newExpl, parameters: defaultValues });
      console.log("if use effect");
    }
  }, [defaultValues]);

  function filterObject(obj, arr) {
    return Object.fromEntries(
      Object.entries(obj).filter(([k]) => arr.includes(k)),
    );
  }

  const handleUpdateParameters = (values) => {
    if (renderFitForm) {
      const parameters = filterObject(values, explainerProperties);
      const fitParameters = filterObject(values, explainerFitProperties);
      setNewExpl((_) => ({
        ...newExpl,
        parameters,
        fit_parameters: fitParameters,
      }));
    } else {
      console.log("update");
      setNewExpl((_) => ({ ...newExpl, parameters: values }));
    }
  };

  useEffect(() => {
    setNextEnabled(true);
  }, []);

  console.log("newexpl");
  console.log(newExpl);

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
                  model={newExpl.explainer_name}
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

ConfigureExplainerStep.propTypes = {
  newExpl: PropTypes.shape({
    name: PropTypes.string,
    explainer_name: PropTypes.string,
    dataset_id: PropTypes.number,
    parameters: PropTypes.object,
    fit_parameters: PropTypes.object,
  }),
  setNewExpl: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  scope: PropTypes.string.isRequired,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
};

export default ConfigureExplainerStep;
