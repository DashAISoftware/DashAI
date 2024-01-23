import SettingsIcon from "@mui/icons-material/Settings";
import {
  Box,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
} from "@mui/material";
import { GridActionsCellItem } from "@mui/x-data-grid";
import PropTypes from "prop-types";
import React, { useState } from "react";
import useModels from "../../pages/experiments/hooks/useModels";
import ParameterForm from "../configurableObject/ParameterForm";
/**
 * This component handles the configuration of a single model
 * @param {string} modelToConfigure name of the model to configure
 * @param {function} updateParameters updates the parameters of the model to configure in the modal state (newExp.runs)
 * @param {object} paramsInitialValues Initial values for the model to be configured, used so that the user can edit the parameters,
 * picking up from the last time they configured.
 */
function EditModelDialog({
  modelToConfigure,
  updateParameters,
  paramsInitialValues,
}) {
  const [open, setOpen] = useState(false);
  const { schema: modelSchema, loading } = useModels({
    selectedModel: modelToConfigure,
  });

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

EditModelDialog.propTypes = {
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

export default EditModelDialog;
