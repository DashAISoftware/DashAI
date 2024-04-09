/* eslint-disable react/prop-types */
import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import React from "react";
import FormSchemaContainer from "./FormSchemaContainer";
import FormSchemaHeader from "./FormSchemaHeader";
// eslint-disable-next-line react/prop-types
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
        sx: { width: { md: 820 }, maxHeight: 900, maxWidth: 2000 },
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

export default FormSchemaDialog;
