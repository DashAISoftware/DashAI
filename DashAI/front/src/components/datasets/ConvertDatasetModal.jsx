import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem } from "@mui/x-data-grid";
import SettingsIcon from "@mui/icons-material/Settings";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  TextField,
  Typography,
  MenuItem,
} from "@mui/material";
import { AddCircleOutline as AddIcon } from "@mui/icons-material";
import { getComponents as getComponentsRequest } from "../../api/component";
import { getModelSchema as getModelSchemaRequest } from "../../api/oldEndpoints";
import { getFullDefaultValues } from "../../api/values";
import uuid from "react-uuid";
import { useSnackbar } from "notistack";

function ConvertDatasetModal({ datasetId, name }) {
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [name2, setName] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [compatibleModels, setCompatibleModels] = useState([]);
  const [models, setModels] = useState([]); // models added to the experiment

  const getCompatibleModels = async () => {
    try {
      const models = await getComponentsRequest({
        selectTypes: ["Model"],
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
    setName("");
    setSelectedModel("");
    setModels([...models, newModel]);
  };

  // in mount, fetches the compatible models with the previously selected task
  useEffect(() => {
    getCompatibleModels();
  }, []);

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="convert-button"
        icon={<SettingsIcon />}
        label="Convert"
        onClick={() => setOpen(true)}
        sx={{ color: "text.primary" }}
      />
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullWidth
        maxWidth={"md"}
      >
        <DialogTitle>Convert dataset</DialogTitle>
        <DialogContent>
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
                    value={name2}
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
              <Typography variant="subtitle1" component="h3">
                PRUEBA
              </Typography>
            </Grid>
          </Grid>
        </DialogContent>

        {/* Actions - Save */}
        <DialogActions>
          <Button
            autoFocus
            variant="contained"
            color="primary"
            disabled={false}
          >
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}

ConvertDatasetModal.propTypes = {
  datasetId: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default ConvertDatasetModal;
