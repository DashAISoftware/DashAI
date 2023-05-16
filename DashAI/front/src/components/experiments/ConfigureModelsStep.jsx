import React, { useState } from "react";
import PropTypes from "prop-types";
import { Button, Grid, MenuItem, TextField, Typography } from "@mui/material";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
// import { getModelSchema as getModelSchemaRequest } from "../../api/oldEndpoints";
// import { useSnackbar } from "notistack";
import ModelsTable from "./ModelsTable";

function ConfigureModelsStep({ newExp, setNewExp, setNextEnabled }) {
  // const { enqueueSnackbar } = useSnackbar();
  const [modelNickname, setModelNickname] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  // const [objectSchema, setObjectSchema] = useState("");
  const [modelsInExperiment, setModelsInExperiment] = useState([]);
  const compatibleModels = [
    "KNeighborsClassifier",
    "RandomForestClassifier",
    "SVC",
    "numericalwrapperfortext",
    "tcTransformerEngSpa",
  ];

  const getNewId = () => {
    if (modelsInExperiment.length === 0) {
      return 0;
    }
    return (
      1 +
      modelsInExperiment.reduce((max, modelObj) => {
        return modelObj.id > max ? modelObj.id : max;
      }, -Infinity)
    );
  };

  const handleAdd = () => {
    const newModel = {
      id: getNewId(),
      nickname: modelNickname,
      type: selectedModel,
    };
    setModelsInExperiment([...modelsInExperiment, newModel]);
    setModelNickname("");
    setSelectedModel("");
  };

  const textFieldWidth = "32vw";
  // const getObjectSchema = async () => {
  //   // setLoading(true);
  //   try {
  //     const schema = await getModelSchemaRequest(selectedModel);
  //     setObjectSchema(schema);
  //   } catch (error) {
  //     enqueueSnackbar("Error while trying to obtain model schema", {
  //       variant: "error",
  //       anchorOrigin: {
  //         vertical: "top",
  //         horizontal: "right",
  //       },
  //     });
  //     if (error.response) {
  //       console.error("Response error:", error.message);
  //     } else if (error.request) {
  //       console.error("Request error", error.request);
  //     } else {
  //       console.error("Unkown Error", error.message);
  //     }
  //   } finally {
  //     // setLoading(false);
  //   }
  // };

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
        justifyContent="space-between"
        alignItems="center"
        sx={{ mb: 4 }}
      >
        <Grid item xs={12}>
          <Typography variant="subtitle1" component="h3" sx={{ mb: 3 }}>
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
            onClick={handleAdd}
            sx={{ height: "3.6vw", ml: 3 }}
          >
            Add
          </Button>
        </Grid>
        <Grid item xs={12} sx={{ mt: 3 }}>
          <ModelsTable
            models={modelsInExperiment}
            setModels={setModelsInExperiment}
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
