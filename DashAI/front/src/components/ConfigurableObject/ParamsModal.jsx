import React from "react";
import PropTypes from "prop-types";
import { Dialog, DialogContent, DialogTitle, IconButton } from "@mui/material";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
// import ParameterForm from "../ParameterForm";
import ParameterForm from "./ParameterForm";
import SplitsParams from "./SplitsParams";

function ParamsModal({
  dataloader,
  paramsSchema,
  onSubmit,
  showModal,
  setShowModal,
  showSplitConfig,
  setSplitConfig,
  showMoreOptions,
  setShowMoreOptions,
  setShowNameModal,
  showSplitsError,
  setShowUploadModal,
}) {
  /*
      To show the dataloader's parameters to be able to upload the data,
      is displayed a modal with ParameterForm, but inside this modal
      it is the splits div there, passed like a extra section.
     */
  const handleBack = () => {
    setShowModal(false);
    setShowNameModal(true);
  };
  const handleClose = (event, reason) => {
    // prevents modal closing when there is a backdrop click
    if (reason && reason === "backdropClick") {
      return;
    }
    setShowModal(false);
    setShowUploadModal(true);
  };
  return (
    <Dialog open={showModal} onClose={handleClose}>
      <DialogTitle>
        <IconButton onClick={handleBack}>
          <ArrowBackIosNewIcon />
        </IconButton>
        {dataloader}
      </DialogTitle>
      <DialogContent>
        <ParameterForm
          parameterSchema={paramsSchema}
          onFormSubmit={(values) => {
            onSubmit(dataloader, values);
            handleClose();
          }}
          extraOptions={
            <div style={{ marginBottom: "15px" }}>
              {paramsSchema.splits !== undefined ? (
                <SplitsParams
                  paramsSchema={paramsSchema.splits}
                  onSubmit={onSubmit} // TODO: build json to submit
                  showSplitConfig={showSplitConfig}
                  setSplitConfig={setSplitConfig}
                  showMoreOptions={showMoreOptions}
                  setShowMoreOptions={setShowMoreOptions}
                  showSplitsError={showSplitsError}
                />
              ) : null}
            </div>
          }
          getValues={
            paramsSchema.properties.splits_in_folders !== undefined
              ? ["splits_in_folders", setSplitConfig]
              : null
          }
          submitButton
        />
      </DialogContent>
    </Dialog>
  );
}
ParamsModal.propTypes = {
  dataloader: PropTypes.string.isRequired,
  paramsSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
  ).isRequired,
  onSubmit: PropTypes.func.isRequired,
  showModal: PropTypes.bool.isRequired,
  setShowModal: PropTypes.func.isRequired,
  showSplitConfig: PropTypes.bool.isRequired,
  setSplitConfig: PropTypes.func.isRequired,
  showMoreOptions: PropTypes.bool.isRequired,
  setShowMoreOptions: PropTypes.func.isRequired,
  setShowNameModal: PropTypes.func.isRequired,
  showSplitsError: PropTypes.bool.isRequired,
  setShowUploadModal: PropTypes.func.isRequired,
};

export default ParamsModal;
