import { Dialog, DialogContent, DialogTitle } from "@mui/material";
import React from "react";
import { ModelSchemaProvider } from "../../contexts/schema";
import ModelSchemaHeader from "./ModelSchemaHeader";
// eslint-disable-next-line react/prop-types
function ModelSchemaDialog({ modelToConfigure, open, setOpen, children }) {
  const handleClose = () => setOpen(false);
  return (
    <Dialog
      open={open}
      onClose={handleClose}
      PaperProps={{ sx: { width: { md: 500 }, maxHeight: 900 } }}
    >
      <ModelSchemaProvider>
        <>
          <DialogTitle>
            <ModelSchemaHeader
              title={`${modelToConfigure} Model`}
              onClose={handleClose}
            />
          </DialogTitle>
          <DialogContent>
            {React.cloneElement(children, { onClose: handleClose })}
          </DialogContent>
        </>
      </ModelSchemaProvider>
    </Dialog>
  );
}

export default ModelSchemaDialog;
