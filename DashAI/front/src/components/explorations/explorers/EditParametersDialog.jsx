import React, { useState } from "react";
import PropTypes from "prop-types";

import SettingsIcon from "@mui/icons-material/Settings";
import { GridActionsCellItem } from "@mui/x-data-grid";

import FormSchemaDialog from "../../shared/FormSchemaDialog";
import FormSchemaWithSelectedModel from "../../shared/FormSchemaWithSelectedModel";
import TooltipedCellItem from "../../shared/TooltipedCellItem";

function EditParametersDialog({
  modelToConfigure,
  updateParameters,
  paramsInitialValues,
}) {
  const [open, setOpen] = useState(false);

  return (
    <React.Fragment>
      <TooltipedCellItem
        key="edit-parameters-button"
        icon={<SettingsIcon />}
        label="Edit Parameters"
        tooltip={`Configure parameters`}
        onClick={() => setOpen(true)}
      />

      {open && (
        <FormSchemaDialog
          modelToConfigure={modelToConfigure}
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
            modelToConfigure={modelToConfigure}
            initialValues={paramsInitialValues}
            onCancel={() => setOpen(false)}
          />
        </FormSchemaDialog>
      )}
    </React.Fragment>
  );
}

EditParametersDialog.propTypes = {
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

export default EditParametersDialog;
