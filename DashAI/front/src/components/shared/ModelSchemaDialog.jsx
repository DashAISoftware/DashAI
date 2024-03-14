import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import React from "react";
import { ModelSchemaProvider } from "../../contexts/schema";
// eslint-disable-next-line react/prop-types
function FormModelSchemaDialog({ modelToConfigure, open, setOpen, children }) {
  return (
    <Dialog
      open={open}
      onClose={() => setOpen(false)}
      PaperProps={{ sx: { width: { md: 500 } } }}
    >
      <DialogTitle>{`${modelToConfigure} parameters`}</DialogTitle>
      <DialogContent>
        <ModelSchemaProvider>{children}</ModelSchemaProvider>
      </DialogContent>
    </Dialog>
  );
}

export default FormModelSchemaDialog;
