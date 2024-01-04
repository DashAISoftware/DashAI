import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem } from "@mui/x-data-grid";
import SettingsIcon from "@mui/icons-material/Settings";
import ParameterForm from "../configurableObject/ParameterForm";
import {
  Box,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
} from "@mui/material";
import { getModelSchema as getModelSchemaRequest } from "../../api/oldEndpoints";
import { useSnackbar } from "notistack";

/**
 * This component handles the configuration of a single converter. Its not working yet,
 * needs the backend to be implemented with the schema of the converter
 */
function EditConverterDialog({
  modelToConfigure,
  updateParameters,
  paramsInitialValues,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [modelSchema, setModelSchema] = useState({});

  const getObjectSchema = async () => {
    setLoading(true);
    try {
      const schema = await getModelSchemaRequest(modelToConfigure);
      setModelSchema(schema);
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain model schema");
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

  // fetches the JSON object on mount
  useEffect(() => {
    getObjectSchema();
  }, []);

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="edit-button"
        icon={<SettingsIcon />}
        label="Edit"
        onClick={() => setOpen(true)}
      />
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>{`${modelToConfigure} parameters`}</DialogTitle>

        <DialogContent>
          <Box sx={{ px: 4, overflow: "auto" }}>
            {/* Parameter form to configure the model */}
            <Grid container direction={"column"} alignItems={"center"}>
              {loading ? (
                <CircularProgress color="inherit" />
              ) : (
                <ParameterForm
                  parameterSchema={modelSchema}
                  initialValues={paramsInitialValues}
                  onFormSubmit={(values) => {
                    updateParameters(values);
                    setOpen(false);
                  }}
                  submitButton
                />
              )}
            </Grid>
          </Box>
        </DialogContent>
      </Dialog>
    </React.Fragment>
  );
}

EditConverterDialog.propTypes = {
  modelToConfigure: PropTypes.string.isRequired,
  updateParameters: PropTypes.func.isRequired,
  paramsInitialValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.number,
      PropTypes.object,
    ]),
  ),
};

export default EditConverterDialog;
