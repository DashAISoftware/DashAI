import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Button, Grid, MenuItem, TextField, Typography } from "@mui/material";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import { getComponents as getComponentsRequest } from "../../api/component";
import { getModelSchema as getModelSchemaRequest } from "../../api/oldEndpoints";
import { useSnackbar } from "notistack";
import ModelsTable from "./ModelsTable";
import { getFullDefaultValues } from "../../api/values";
import uuid from "react-uuid";

/**
 * Step of the experiment modal: add models to the experiment and configure its parameters
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the modal
 */
function ConfigureModelsStep({ newExp, setNewExp, setNextEnabled }) {
  const { enqueueSnackbar } = useSnackbar();
  const [name, setName] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [compatibleModels, setCompatibleModels] = useState([]);

  const getCompatibleModels = async () => {
    try {
      const models = await getComponentsRequest({
        selectTypes: ["Model"],
        relatedComponent: newExp.task_name,
      });
      setCompatibleModels(models);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain compatible models");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const getModelSchema = async () => {
    try {
      const schema = await getModelSchemaRequest(selectedModel);
      return schema;
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain model schema");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const handleAddButton = async () => {
    // sets the default values of the newly added model, making optional the parameter configuration
    const schema = await getModelSchema();
    const schemaDefaultValues = await getFullDefaultValues(schema);
    const newModel = {
      id: uuid(),
      name,
      model: selectedModel,
      params: schemaDefaultValues,
    };
    setNewExp({ ...newExp, runs: [newModel, ...newExp.runs] });
    setName("");
    setSelectedModel("");
  };

  // checks if there is at least 1 model added to enable the "Next" button
  useEffect(() => {
    if (newExp.runs.length > 0) {
      setNextEnabled(true);
    } else {
      setNextEnabled(false);
    }
  }, [newExp]);

  // in mount, fetches the compatible models with the previously selected task
  useEffect(() => {
    getCompatibleModels();
  }, []);

  return (
    <Grid
      container
      direction="row"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={2}
    >
      <Grid item xs={12}>
        <Typography variant="subtitle1" component="h3">
          Add models to your experiment
        </Typography>
      </Grid>

      {/* Form to add a single model to the experiment */}
      <Grid item xs={12}>
        <Grid container direction="row" columnSpacing={3} wrap="nowrap">
          <Grid item xs={4} md={12}>
            <TextField
              label="Name (optional)"
              value={name}
              onChange={(e) => setName(e.target.value)}
              fullWidth
            />
          </Grid>

          <Grid item xs={4} md={12}>
            <TextField
              select
              label="Select a model to add"
              value={selectedModel}
              onChange={(e) => {
                setSelectedModel(e.target.value);
              }}
              fullWidth
            >
              {compatibleModels.map((model) => (
                <MenuItem key={model.name} value={model.name}>
                  {model.name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={1} md={2}>
            <Button
              variant="outlined"
              disabled={selectedModel === ""}
              startIcon={<AddIcon />}
              onClick={handleAddButton}
              sx={{ height: "100%" }}
            >
              Add
            </Button>
          </Grid>
        </Grid>
      </Grid>

      {/* Models table */}
      <Grid item xs={12}>
        <ModelsTable newExp={newExp} setNewExp={setNewExp} />
      </Grid>
    </Grid>
  );
}

ConfigureModelsStep.propTypes = {
  newExp: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    dataset: PropTypes.object,
    task_name: PropTypes.string,
    input_columns: PropTypes.arrayOf(PropTypes.number),
    output_columns: PropTypes.arrayOf(PropTypes.number),
    splits: PropTypes.shape({
      has_changed: PropTypes.bool,
      is_random: PropTypes.bool,
      training: PropTypes.number,
      validation: PropTypes.number,
      testing: PropTypes.number,
    }),
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default ConfigureModelsStep;
