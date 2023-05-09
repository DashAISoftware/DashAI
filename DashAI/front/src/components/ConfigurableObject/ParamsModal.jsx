import React from "react";
import PropTypes from "prop-types";
import { Dialog, DialogContent, DialogTitle, IconButton } from "@mui/material";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import ParameterForm from "./ParameterForm";
import SplitsParams from "./SplitsParams";
/**
 * This component is used to render the configuration for data loaders,
 * which are a special case of configurable objects with varying properties in their JSON representation.
 * It renders a modal containing a ParameterForm with extraOptions.
 * @param {string} dataloader name of the dataloader
 * @param {object} paramsSchema JSON object that describes a configurable object
 * @param {function} onSubmit function to submit the parameters of the dataloader
 * @param {bool} showModal true to show the modal that contins the form, false to not show it
 * @param {function} setShowModal function to change the state of showModal
 * @param {bool} showSplitConfig shows or hides the split section, depending on user input
 * @param {function} setSplitConfig function to change the state of showSplitConfig
 * @param {bool} showMoreOptions indicates if the form shows a more options section
 * @param {function} setShowMoreOptions function to change the state of showMoreOptions
 * @param {function} setShowNameModal TODO
 * @param {bool} showSplitsError
 * @param {function} setShowUploadModal TODO
 */
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
      {/* back button and name of the dataloader */}
      <DialogTitle>
        <IconButton onClick={handleBack}>
          <ArrowBackIosNewIcon />
        </IconButton>
        {dataloader}
      </DialogTitle>

      {/* Parameter form with extraOptions to handle splits */}
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
