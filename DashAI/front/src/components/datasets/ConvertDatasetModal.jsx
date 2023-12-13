import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem, DataGrid } from "@mui/x-data-grid";
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
  Stepper,
  Step,
  StepButton,
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
  const [selectedModel, setSelectedModel] = useState("");
  const [compatibleModels, setCompatibleModels] = useState([]);
  const [models, setModels] = useState([]); // models added to the experiment
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    { name: "convertDataset", label: "Convert the dataset" },
    { name: "previewconfirm", label: "Preview and confirm" },
  ];

  const handleStepButton = (stepIndex) => () => {
    setActiveStep(stepIndex);
  };

  const getCompatibleModels = async () => {
    try {
      const models = await getComponentsRequest({
        selectTypes: ["Converter"],
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
    setSelectedModel("");
    setModels([...models, newModel]);
  };

  // in mount, fetches the compatible models with the previously selected task
  useEffect(() => {
    getCompatibleModels();
  }, []);

  const rows = [
    { id: 1, firstName: "John", lastName: "Doe", age: 25 },
    { id: 2, firstName: "Jane", lastName: "Doe", age: 30 },
    // ... más filas
  ];

  const columns = [
    { field: "id", headerName: "ID", width: 70 },
    { field: "firstName", headerName: "First Name", width: 150 },
    { field: "lastName", headerName: "Last Name", width: 150 },
    { field: "age", headerName: "Age", type: "number", width: 70 },
    // ... más columnas
  ];

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
        <DialogTitle>
          <Grid container direction={"row"} alignItems={"center"}>
            <Grid item xs={12} md={3}>
              <Typography
                variant="h6"
                component={"h3"}
                sx={{ mb: { sm: 2, md: 0 } }}
              >
                Data Converter
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Stepper
                nonLinear
                activeStep={activeStep}
                sx={{ maxWidth: "100%" }}
              >
                {steps.map((step, index) => (
                  <Step
                    key={`${step.name}`}
                    completed={activeStep > index}
                    disabled={activeStep < index}
                  >
                    <StepButton
                      color="inherit"
                      onClick={handleStepButton(index)}
                    >
                      {step.label}
                    </StepButton>
                  </Step>
                ))}
              </Stepper>
            </Grid>
            {/* Actions - Save */}
            <DialogActions>
              <Button
                autoFocus
                variant="contained"
                color="primary"
                disabled={false}
              >
                Save Preview
              </Button>
            </DialogActions>
          </Grid>
        </DialogTitle>
        <DialogContent dividers>
          <Grid
            container
            direction="row"
            justifyContent="space-around"
            alignItems="stretch"
            spacing={2}
          >
            <Grid item xs={12}>
              <Typography variant="subtitle1" component="h3">
                Add converters to your experiment
              </Typography>
            </Grid>

            {/* Form to add a single model to the experiment */}
            <Grid item xs={12}>
              <Grid
                container
                direction="row"
                columnSpacing={3}
                wrap="nowrap"
                justifyContent="flex-start"
              >
                <Grid item xs={4} md={12}>
                  <TextField
                    select
                    label="Select a converter to add"
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

                <Grid item xs={4} md={10}>
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
                {/* Datasets Table */}
                <DataGrid
                  rows={rows}
                  columns={columns}
                  initialState={{
                    pagination: {
                      paginationModel: {
                        pageSize: 5,
                      },
                    },
                  }}
                  sortModel={[{ field: "id", sort: "desc" }]}
                  pageSize={5}
                  pageSizeOptions={[5, 10]}
                  disableRowSelectionOnClick
                  autoHeight
                />
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
            Save as
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
