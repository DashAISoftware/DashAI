import React, { useState } from "react";
import PropTypes from "prop-types";
import { GridActionsCellItem } from "@mui/x-data-grid";
import { Settings } from "@mui/icons-material";
import FormSchemaDialog from "../shared/FormSchemaDialog";
import FormSchemaWithSelectedModel from "../shared/FormSchemaWithSelectedModel";

const ConverterEditorModal = ({
  converterToConfigure,
  updateParameters,
  paramsInitialValues,
}) => {
  const [open, setOpen] = useState(false);

  const handleOnSave = (paramsAndValues) => {
    updateParameters(paramsAndValues);
    setOpen(false);
  };

  return (
    <React.Fragment>
      <GridActionsCellItem
        key="edit-button"
        icon={<Settings />}
        label="Set"
        onClick={() => setOpen(true)}
      >
        Set
      </GridActionsCellItem>
      <FormSchemaDialog
        modelToConfigure={converterToConfigure}
        open={open}
        setOpen={setOpen}
        onFormSubmit={handleOnSave}
      >
        <FormSchemaWithSelectedModel
          onFormSubmit={handleOnSave}
          modelToConfigure={converterToConfigure}
          initialValues={paramsInitialValues}
          onCancel={() => setOpen(false)}
        />
      </FormSchemaDialog>
    </React.Fragment>
  );
};

ConverterEditorModal.propTypes = {
  converterToConfigure: PropTypes.string,
  updateParameters: PropTypes.func.isRequired,
  paramsInitialValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.number,
      PropTypes.array,
    ]),
  ),
};

ConverterEditorModal.defaultProps = {
  converterToConfigure: "",
  paramsInitialValues: {},
};

export default ConverterEditorModal;
