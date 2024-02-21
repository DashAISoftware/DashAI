import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem, DataGrid } from "@mui/x-data-grid";
import {
  getDatasetSample as getDatasetSampleRequest,
  getDatasetTypes as getDatasetTypesRequest,
} from "../../api/datasets";
import SettingsIcon from "@mui/icons-material/Settings";
import {
  Button,
  ButtonGroup,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  TextField,
  Typography,
  MenuItem,
} from "@mui/material";
import TouchAppIcon from "@mui/icons-material/TouchApp";
import { getComponents as getComponentsRequest } from "../../api/component";
import uuid from "react-uuid";
import { useSnackbar } from "notistack";
import EditConverterDialog from "./EditConverterDialog";
import {
  enqueueConverterJob as enqueueConverterJobRequest,
  startJobQueue as startJobQueueRequest,
} from "../../api/job";

/**
 * This component renders a modal that takes the user through the process of applying
 * a converter to a dataset.
 */
function ConvertDatasetModal({
  uploadedDataset,
  setNextEnabled,
  datasetUploaded,
  columnsSpec,
  setColumnsSpec,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [selectedConverter, setSelectedConverter] = useState({
    id: 0,
    name: "",
    converter: null,
    params: {},
    schema: {},
  });
  const [compatibleConverters, setCompatibleConverters] = useState([]);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [displayApply, setDisplayApply] = useState(false);
  const [openConverterParams, setOpenConverterParams] = useState(false);

  // A function to get the compatible converters with the selected dataset
  const getcompatibleConverters = async () => {
    try {
      const converters = await getComponentsRequest({
        selectTypes: ["Converter"],
      });
      setCompatibleConverters(converters);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain compatible converters");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  // After the converter is applied, the EditConverterDialog is opened
  useEffect(() => {
    if (displayApply) {
      setDisplayApply(false);
    }
  }, [displayApply]);

  // A function to get the dataset info.
  const getDatasetInfo = async () => {
    setLoading(true);
    try {
      const dataset = await getDatasetSampleRequest(uploadedDataset.id);
      const types = await getDatasetTypesRequest(uploadedDataset.id);
      const rowsArray = Object.keys(dataset).map((name, idx) => {
        return {
          id: idx,
          columnName: name,
          example: dataset[name][0],
          columnType: types[name].type,
          dataType: types[name].dtype,
        };
      });
      setRows(rowsArray);
      setColumnsSpec(types);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain the dataset.");
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

  // in mount, fetches the compatible converters with the previously selected task
  useEffect(() => {
    getcompatibleConverters();
  }, []);

  const getFullDefaultValues = (schema) => {
    const defaultValues = {};
    const properties = schema.properties;
    for (const param of Object.keys(properties)) {
      const val = properties[param].oneOf[0].default;
      if (val !== undefined) {
        defaultValues[param] = val;
      } else {
        defaultValues[param] = "";
      }
    }
    return defaultValues;
  };

  const columns = [
    {
      field: "columnName",
      headerName: "Column name",
      minWidth: 200,
      editable: false,
    },
    {
      field: "example",
      headerName: "Example",
      minWidth: 200,
      editable: false,
    },
    {
      field: "columnType",
      headerName: "Column type",
      minWidth: 200,
      editable: true,
    },
    {
      field: "dataType",
      headerName: "Data type",
      minWidth: 200,
      editable: true,
    },
  ];

  useEffect(() => {
    if (datasetUploaded) {
      getDatasetInfo();
      setNextEnabled(true);
    }
  }, [datasetUploaded]);

  const handleCloseDialog = () => {
    setOpen(false);
  };

  const handleOpenConverterParams = () => {
    setOpenConverterParams(true);
  };

  const handleCloseConverterParams = () => {
    setOpenConverterParams(false);
  };

  const enqueueConverterJob = async (
    datasetId,
    converterTypeName,
    newDatasetName,
    converterParams,
  ) => {
    try {
      await enqueueConverterJobRequest(
        datasetId,
        converterTypeName,
        newDatasetName,
        converterParams,
      );
      return false; // return false for sucess
    } catch (error) {
      enqueueSnackbar(
        `Error while trying to apply the converter ${converterTypeName}`,
      );
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
      return true; // return true for error
    }
  };

  const startJobQueue = async () => {
    try {
      await startJobQueueRequest();
    } catch (error) {
      enqueueSnackbar("Error while trying to start job queue");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const handleExecuteRuns = async (
    datasetId,
    converterTypeName,
    newDatasetName,
    converterParams,
  ) => {
    let enqueueErrors = 0;
    // send runs to the job queue
    const error = await enqueueConverterJob(
      datasetId,
      converterTypeName,
      newDatasetName,
      converterParams,
    );
    enqueueErrors = error ? enqueueErrors + 1 : enqueueErrors;
    // verify that at least one job was succesfully enqueued to start the job queue
    if (enqueueErrors < 1) {
      startJobQueue(true); // true to stop when queue empties
    } else {
      enqueueSnackbar("Error while trying to enqueue the converter job");
    }
  };

  const handleApplyAndSave = () => {
    setOpen(false);
    setSelectedConverter({
      id: 0,
      name: "",
      converter: null,
      params: {},
      schema: {},
    });
    handleExecuteRuns(
      uploadedDataset.id,
      selectedConverter.name,
      name,
      selectedConverter.params,
    );
  };

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="convert-button"
        icon={<SettingsIcon />}
        label="Convert"
        onClick={() => [setOpen(true), getDatasetInfo()]}
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
          </Grid>
        </DialogTitle>
        <DialogContent dividers>
          <Grid
            container
            direction="row"
            justifyContent="space-around"
            alignItems="stretch"
            spacing={1}
          ></Grid>
          <Grid item xs={12}>
            <Typography variant="subtitle1" component="h3" mb={1}>
              Apply converters to your dataset and save a copy of it.
            </Typography>
          </Grid>

          {/* Form to apply a converter to the dataset */}
          <Grid item xs={12}>
            <Grid
              container
              direction="row"
              columnSpacing={3}
              wrap="nowrap"
              mb={1}
            >
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
                  label="Select a converter to add"
                  value={selectedConverter.name}
                  onChange={(e) => {
                    // search the converter in the compatibleConverters array using the name
                    const selected = compatibleConverters.find(
                      (converter) => converter.name === e.target.value,
                    );
                    const schema = selected.schema;
                    const schemaDefaultValues = getFullDefaultValues(schema);
                    const newConverter = {
                      id: uuid(),
                      name: selected.name,
                      converter: selected,
                      params: schemaDefaultValues,
                      schema,
                    };
                    setSelectedConverter(newConverter);
                    handleOpenConverterParams();
                  }}
                  fullWidth
                >
                  {compatibleConverters.map((converter) => (
                    <MenuItem key={converter.name} value={converter.name}>
                      {converter.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={4}>
                <EditConverterDialog
                  converterToConfigure={selectedConverter.name}
                  updateParameters={(values) => {
                    setSelectedConverter({
                      ...selectedConverter,
                      params: values,
                    });
                  }}
                  paramsInitialValues={selectedConverter.params}
                  converterSchema={selectedConverter.schema}
                  open={openConverterParams}
                  handleOpen={handleOpenConverterParams}
                  handleClose={handleCloseConverterParams}
                />
              </Grid>
            </Grid>

            <DialogContent dividers></DialogContent>

            {/* Converters table */}
            <Grid item xs={10}>
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
                  pageSize={5}
                  pageSizeOptions={[5, 10]}
                  loading={loading}
                  disableRowSelectionOnClick
                  autoHeight
                />
              </Typography>
            </Grid>
          </Grid>
        </DialogContent>

        {/* Actions - Back and Save */}
        <DialogActions>
          <ButtonGroup size="large">
            <Button onClick={handleCloseDialog}>Close</Button>
            <Button
              onClick={handleApplyAndSave}
              autoFocus
              variant="contained"
              color="primary"
              startIcon={<TouchAppIcon />}
              disabled={selectedConverter === ""}
            >
              Apply & Save
            </Button>
          </ButtonGroup>
        </DialogActions>
      </Dialog>
    </React.Fragment>
  );
}

ConvertDatasetModal.propTypes = {
  datasetId: PropTypes.number.isRequired,
  name: PropTypes.string.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
  uploadedDataset: PropTypes.object,
  datasetUploaded: PropTypes.bool,
  columnsSpec: PropTypes.object.isRequired,
  setColumnsSpec: PropTypes.func.isRequired,
};

export default ConvertDatasetModal;
