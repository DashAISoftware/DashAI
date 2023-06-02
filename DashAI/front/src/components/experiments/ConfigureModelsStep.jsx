import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Button, Grid, MenuItem, TextField, Typography } from "@mui/material";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import { getModelSchema as getModelSchemaRequest } from "../../api/oldEndpoints";
import { useSnackbar } from "notistack";
import ModelsTable from "./ModelsTable";
import { getFullDefaultValues } from "../../utils/values";
import uuid from "react-uuid";

/**
 * Step of the experiment modal: add models to the experiment and configure its parameters
 * @param {object} newExp object that contains the Experiment Modal state
 * @param {function} setNewExp updates the Eperimento Modal state (newExp)
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the modal
 */
function ConfigureModelsStep({ newExp, setNewExp, setNextEnabled }) {
  const { enqueueSnackbar } = useSnackbar();
  const [modelNickname, setModelNickname] = useState("");
  const [selectedModel, setSelectedModel] = useState("");

  const compatibleModels = [
    "KNeighborsClassifier",
    "RandomForestClassifier",
    "SVC",
    "numericalwrapperfortext",
    "tcTransformerEngSpa",
  ];

  // width for model nickname and model type textfields
  const textFieldWidth = "32vw";

  const getModelSchema = async () => {
    try {
      const schema = await getModelSchemaRequest(selectedModel);
      return schema;
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain model schema", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    }
  };

  const handleAddButton = async () => {
    // sets the default values of the newly added model, making optional the parameter configuration
    const schema = await getModelSchema();
    const schemaDefaultValues = await getFullDefaultValues(schema);
    const newModel = {
      id: uuid(),
      nickname: modelNickname,
      type: selectedModel,
      params: schemaDefaultValues,
    };
    setNewExp({ ...newExp, runs: [...newExp.runs, newModel] });
    setModelNickname("");
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
        <Grid container direction="row" columnSpacing={5}>
          <Grid item>
            <TextField
              label="Nickname (optional)"
              value={modelNickname}
              onChange={(e) => setModelNickname(e.target.value)}
              sx={{ width: textFieldWidth }}
            />
          </Grid>

          <Grid item>
            <TextField
              select
              label="Select a model to add"
              value={selectedModel}
              onChange={(e) => {
                setSelectedModel(e.target.value);
              }}
              sx={{ width: textFieldWidth }}
            >
              {compatibleModels.map((model) => (
                <MenuItem key={model} value={model}>
                  {model}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item>
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
    step: PropTypes.string,
    created: PropTypes.instanceOf(Date),
    last_modified: PropTypes.instanceOf(Date),
    runs: PropTypes.array,
  }),
  setNewExp: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default ConfigureModelsStep;
