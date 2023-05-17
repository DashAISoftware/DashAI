import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { Button, Grid, MenuItem, TextField, Typography } from "@mui/material";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import { getModelSchema as getModelSchemaRequest } from "../../api/oldEndpoints";
import { useSnackbar } from "notistack";
import ModelsTable from "./ModelsTable";
import { getFullDefaultValues } from "../../utils/values";

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
  // const [modelsInExperiment, setModelsInExperiment] = useState([]);

  const compatibleModels = [
    "KNeighborsClassifier",
    "RandomForestClassifier",
    "SVC",
    "numericalwrapperfortext",
    "tcTransformerEngSpa",
  ];

  // width for model nickname and model type textfields
  const textFieldWidth = "32vw";

  // gets a new id for a model by adding 1 to the max id of the current models in the experiment
  const getNewId = () => {
    if (newExp.runs.length === 0) {
      return 0;
    }
    return (
      1 +
      newExp.runs.reduce((max, modelObj) => {
        return modelObj.id > max ? modelObj.id : max;
      }, -Infinity)
    );
  };

  const getModelSchema = async () => {
    // setLoading(true);
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
    } finally {
      // setLoading(false);
    }
  };

  const handleAddButton = async () => {
    // sets the default values of the newly added model, making optional the parameter configuration
    const schema = await getModelSchema();
    const schemaDefaultValues = await getFullDefaultValues(schema);
    const newModel = {
      id: getNewId(),
      nickname: modelNickname,
      type: selectedModel,
      params: schemaDefaultValues,
    };
    setNewExp({ ...newExp, runs: [...newExp.runs, newModel] });
    // setModelsInExperiment([...modelsInExperiment, newModel]);
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

  // fetches the JSON object of the model selected by the user
  // useEffect(() => {
  //   if (selectedModel !== "") {
  //     getObjectSchema();
  //   }
  // }, [selectedModel]);

  // console.log(objectSchema);
  return (
    <React.Fragment>
      <Grid
        container
        direction="row"
        justifyContent="space-around"
        alignItems="stretch"
        spacing={2}
      >
        {/* Form to add a single model to the experiment */}
        <Grid item xs={12}>
          <Typography variant="subtitle1" component="h3" sx={{ mb: 2 }}>
            Add models to your experiment
          </Typography>

          <TextField
            label="Nickname (optional)"
            value={modelNickname}
            onChange={(e) => setModelNickname(e.target.value)}
            sx={{ minWidth: textFieldWidth, mr: 3 }}
          />

          <TextField
            select
            label="Select a model to add"
            value={selectedModel}
            onChange={(e) => {
              setSelectedModel(e.target.value);
            }}
            sx={{ minWidth: textFieldWidth }}
          >
            {compatibleModels.map((model) => (
              <MenuItem key={model} value={model}>
                {model}
              </MenuItem>
            ))}
          </TextField>

          <Button
            variant="outlined"
            disabled={selectedModel === ""}
            startIcon={<AddIcon />}
            onClick={handleAddButton}
            sx={{ height: "55%", ml: 3 }}
          >
            Add
          </Button>
        </Grid>

        {/* Models table */}
        <Grid item xs={12}>
          <ModelsTable
            newExp={newExp}
            setNewExp={setNewExp}
            // models={modelsInExperiment}
            // setModels={setModelsInExperiment}
          />
        </Grid>
      </Grid>
    </React.Fragment>
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
