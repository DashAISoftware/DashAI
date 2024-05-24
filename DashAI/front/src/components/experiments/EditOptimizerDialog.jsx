import React, { useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem } from "@mui/x-data-grid";
import SettingsIcon from "@mui/icons-material/Settings";
import FormSchemaDialog from "../shared/FormSchemaDialog";
import FormSchemaWithSelectedModel from "../shared/FormSchemaWithSelectedModel";

/**
 * This component handles the configuration of a single model
 * @param {string} optimizerToConfigure name of the model to configure
 * @param {function} updateParameters updates the parameters of the optimizer to configure in the modal state (newExp.runs)
 * @param {object} paramsInitialValues Initial values for the model to be configured, used so that the user can edit the parameters,
 * picking up from the last time they configured.
 */
function EditOptimizerDialog({
  optimizerToConfigure,
  updateParameters,
  paramsInitialValues,
}) {
  const [open, setOpen] = useState(false);

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="edit-button"
        icon={<SettingsIcon />}
        label="Edit"
        onClick={() => setOpen(true)}
      />

      <FormSchemaDialog
        modelToConfigure={optimizerToConfigure}
        open={open}
        setOpen={setOpen}
        onFormSubmit={(values) => {
          updateParameters(values);
          setOpen(false);
        }}
      >
        <FormSchemaWithSelectedModel
          onFormSubmit={(values) => {
            updateParameters(values);
            setOpen(false);
          }}
          modelToConfigure={optimizerToConfigure}
          initialValues={paramsInitialValues}
          onCancel={() => setOpen(false)}
        />
      </FormSchemaDialog>
    </React.Fragment>
  );
}

EditOptimizerDialog.propTypes = {
  optimizerToConfigure: PropTypes.string.isRequired,
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

export default EditOptimizerDialog;
