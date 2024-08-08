import React, { useState } from "react";
import PropTypes from "prop-types";
import { Button } from "@mui/material";
import { AssignmentTurnedIn } from "@mui/icons-material";
import FormSchemaDialog from "../shared/FormSchemaDialog";
import FormSchemaWithSelectedModel from "../shared/FormSchemaWithSelectedModel";

const ConverterEditorModal = ({ newConverter, saveConverter }) => {
  const [open, setOpen] = useState(false);

  const handleOnSave = (converterSchemaWithSelectedValues) => {
    const parameters = Object.keys(
      converterSchemaWithSelectedValues.properties,
    ).reduce((acc, property) => {
      acc[property] =
        converterSchemaWithSelectedValues[property] ??
        converterSchemaWithSelectedValues.properties[property].placeholder; // If the value wasn't set, use the placeholder
      return acc;
    }, {});
    saveConverter(parameters);
    setOpen(false);
  };

  return (
    <React.Fragment>
      <Button
        onClick={() => setOpen(true)}
        autoFocus
        fullWidth
        variant="outlined"
        color="primary"
        key="edit-button"
        startIcon={<AssignmentTurnedIn />}
        disabled={!newConverter.name}
        sx={{
          height: "100%",
        }}
      >
        Set
      </Button>
      <FormSchemaDialog
        modelToConfigure={newConverter?.name}
        open={open}
        setOpen={setOpen}
        onFormSubmit={handleOnSave}
      >
        <FormSchemaWithSelectedModel
          onFormSubmit={handleOnSave}
          modelToConfigure={newConverter?.name}
          initialValues={newConverter?.schema}
          onCancel={() => setOpen(false)}
        />
      </FormSchemaDialog>
    </React.Fragment>
  );
};

ConverterEditorModal.propTypes = {
  newConverter: PropTypes.object,
  saveConverter: PropTypes.func.isRequired,
  open: PropTypes.bool,
  setOpen: PropTypes.func,
};

ConverterEditorModal.defaultProps = {
  newConverter: null,
  open: false,
  setOpen: () => {},
};

export default ConverterEditorModal;
