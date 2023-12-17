import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  GridActionsCellItem,
  DataGrid,
  useGridApiContext,
} from "@mui/x-data-grid";
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
import { getModelSchema as getModelSchemaRequest } from "../../api/oldEndpoints";
import { getFullDefaultValues } from "../../api/values";
import uuid from "react-uuid";
import { useSnackbar } from "notistack";
import { dataTypesList, columnTypesList } from "../../utils/typesLists";
import SelectTypeCell from "../custom/SelectTypeCell";
import EditConverterDialog from "./EditConverterDialog";

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
  const [selectedConverter, setSelectedConverter] = useState("");
  const [compatibleConverters, setCompatibleConverters] = useState([]);
  const [converters, setConverters] = useState([]); // models added to the experiment
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [displayApply, setDisplayApply] = useState(false);

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

  /**
   * This function and handle apply button are not working yet. They are though to be
   * used to get the converter schemas to configure the parameters of a converter.
   */
  const getConverterSchema = async () => {
    try {
      const schema = await getModelSchemaRequest(selectedConverter);
      return schema;
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain converter schema");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const handleApplyButton = async () => {
    // sets the default values of the newly added model, making optional the parameter configuration
    const schema = await getConverterSchema();
    const schemaDefaultValues = await getFullDefaultValues(schema);
    const newConverter = {
      id: uuid(),
      name,
      model: selectedConverter,
      params: schemaDefaultValues,
    };
    setSelectedConverter("");
    setConverters([...converters, newConverter]);
    setDisplayApply(true);
  };

  // After the converter is applied, the EditConverterDialog is opened
  useEffect(() => {
    if (displayApply) {
      EditConverterDialog.setOpen(true);
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

  const updateCellValue = async (id, field, newValue) => {
    const apiRef = useGridApiContext();
    await apiRef.current.setEditCellValue({ id, field, value: newValue });
    apiRef.current.stopCellEditMode({ id, field });

    setRows((prevRows) =>
      prevRows.map((row) =>
        row.id === id ? { ...row, [field]: newValue } : row,
      ),
    );

    const columnName = rows.find((row) => row.id === id)?.columnName;
    const updateColumns = { ...columnsSpec };

    if (field === "dataType") {
      updateColumns[columnName].dtype = newValue;
    } else if (field === "columnType") {
      updateColumns[columnName].type = newValue;
    }

    setColumnsSpec(updateColumns);
  };

  const renderSelectCell = (params, options) => {
    return (
      <SelectTypeCell
        id={params.id}
        value={params.value}
        field={params.field}
        options={options}
        updateValue={updateCellValue}
      />
    );
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
      renderEditCell: (params) => renderSelectCell(params, columnTypesList),
      minWidth: 200,
      editable: true,
    },
    {
      field: "dataType",
      headerName: "Data type",
      renderEditCell: (params) => renderSelectCell(params, dataTypesList),
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

  const handleNextButton = () => {
    // uploadNewExperiment();
    handleCloseDialog();
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
            <Typography variant="subtitle1" component="h3">
              Apply converters to your dataset and save a copy of it.
            </Typography>
          </Grid>

          {/* Form to apply a converter to the dataset */}
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
                  label="Select a converter to add"
                  value={selectedConverter}
                  onChange={(e) => {
                    setSelectedConverter(e.target.value);
                  }}
                  fullWidth
                >
                  {compatibleConverters.map((model) => (
                    <MenuItem key={model.name} value={model.name}>
                      {model.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>

              <Grid item xs={4} md={10}>
                <Button
                  variant="outlined"
                  disabled={selectedConverter === ""}
                  startIcon={<TouchAppIcon />}
                  onClick={handleApplyButton}
                  sx={{ height: "100%" }}
                >
                  Apply
                </Button>
              </Grid>
            </Grid>

            <DialogContent dividers></DialogContent>

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
              onClick={handleNextButton}
              autoFocus
              variant="contained"
              color="primary"
            >
              Save
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
