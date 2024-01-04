import React from "react";
import PropTypes from "prop-types";
import SettingsIcon from "@mui/icons-material/Settings";
import ParameterForm from "../configurableObject/ParameterForm";
import {
  Box,
  Button,
  Dialog,
  DialogContent,
  DialogTitle,
  Grid,
} from "@mui/material";

/**
 * This component handles the configuration of a single converter. Its not working yet,
 * needs the backend to be implemented with the schema of the converter
 */
function EditConverterDialog({
  converterToConfigure,
  updateParameters,
  paramsInitialValues,
  converterSchema,
  open,
  handleOpen,
  handleClose
}) {

  return (
    <React.Fragment>
      <Button
        onClick={() => handleOpen()}
        autoFocus
        variant="outlined"
        color="primary"
        label="Edit"
        key={"edit-button"}
        startIcon={<SettingsIcon />}
        // TODO: Find a better way to maximize the y size of the button
        sx={{ height: "100%" }}
        disabled={converterToConfigure === ""}
      >
        Parameters
      </Button>
      <Dialog open={open} onClose={() => handleClose()}>
        <DialogTitle>{`${converterToConfigure} parameters`}</DialogTitle>

        <DialogContent>
          <Box sx={{ px: 4, overflow: "auto" }}>
            {/* Parameter form to configure the model */}
            <Grid container direction={"column"} alignItems={"center"}>
              <ParameterForm
                parameterSchema={converterSchema}
                initialValues={paramsInitialValues}
                onFormSubmit={(values) => {
                  updateParameters(values);
                  handleClose();
                }}
                submitButton
              />
            </Grid>
          </Box>
        </DialogContent>
      </Dialog>
    </React.Fragment>
  );
}

EditConverterDialog.propTypes = {
  converterToConfigure: PropTypes.string.isRequired,
  updateParameters: PropTypes.func.isRequired,
  paramsInitialValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.number,
      PropTypes.object,
    ]),
  ),
  converterSchema: PropTypes.object,
  open: PropTypes.bool,
  handleOpen: PropTypes.func.isRequired,
  handleClose: PropTypes.func.isRequired,
};

export default EditConverterDialog;
