import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import React from "react";
import FormSchemaContainer from "./FormSchemaContainer";
import FormSchemaHeader from "./FormSchemaHeader";
import PropTypes from "prop-types";

/**
 * This component is a dialog for configuring a model, it wraps the form schema and the header.
 * @param {string} modelToConfigure - The model to configure
 * @param {boolean} open - The open state of the dialog
 * @param {function} setOpen - The function to set the open state of the dialog
 * @param {function} onFormSubmit - The function to submit the form
 * @param {node} children - The children of the dialog
 */

function FormSchemaDialog({
  modelToConfigure,
  open,
  setOpen,
  onFormSubmit,
  children,
}) {
  const handleClose = () => setOpen(false);
  return (
    <Dialog
      open={open}
      onClose={handleClose}
      PaperProps={{
        sx: { width: { md: 820 }, maxHeight: 650, maxWidth: 2000 },
      }}
    >
      <FormSchemaContainer>
        <DialogTitle>
          <FormSchemaHeader
            title={`${modelToConfigure} Model`}
            onClose={handleClose}
            onFormSubmit={onFormSubmit}
          />
        </DialogTitle>
        <DialogContent>
          {React.cloneElement(children, { onClose: handleClose })}
        </DialogContent>
      </FormSchemaContainer>
    </Dialog>
  );
}

FormSchemaDialog.propTypes = {
  modelToConfigure: PropTypes.string.isRequired,
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  onFormSubmit: PropTypes.func.isRequired,
  children: PropTypes.node.isRequired,
};

export default FormSchemaDialog;
