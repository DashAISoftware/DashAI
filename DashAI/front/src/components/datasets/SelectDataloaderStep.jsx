import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";
import { getCompatibleDataloaders as getCompatibleDataloadersRequest } from "../../api/dataloader";
import ItemSelector from "./ItemSelector";
import { DialogContentText } from "@mui/material";

/**
 * This component renders a list of dataloaders and allows the user to select one.
 * @param {object} newDataset An object that stores all the important states for the dataset modal.
 * @param {function} setNewDataset function that modifies newDataset state
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the dataset modal.
 */
function SelectDataloaderStep({ newDataset, setNewDataset, setNextEnabled }) {
  const { enqueueSnackbar } = useSnackbar();

  const [dataloaders, setDataloaders] = useState([]);
  const [selectedDataloader, setSelectedDataloader] = useState({});
  const [loading, setLoading] = useState(true);

  async function getCompatibleDataloaders() {
    setLoading(true);
    try {
      const dataloaders = await getCompatibleDataloadersRequest(
        newDataset.task_name,
      );
      setDataloaders(dataloaders);
      if (newDataset.dataloader !== "") {
        const previouslySelectedDataloader = dataloaders.find(
          (dataloader) => dataloader.class === newDataset.dataloader,
        );
        setSelectedDataloader(previouslySelectedDataloader);
      }
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain compatible dataloaders", {
        variant: "error",
        anchorOrigin: {
          vertical: "top",
          horizontal: "right",
        },
      });
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  }

  // updates the modal state with the name of the dataloader that is selected by the user
  useEffect(() => {
    if ("class" in selectedDataloader) {
      setNewDataset({ ...newDataset, dataloader: selectedDataloader.class });
      setNextEnabled(true);
    }
  }, [selectedDataloader]);

  // fetches the available dataloaders
  useEffect(() => {
    getCompatibleDataloaders();
  }, []);
  return (
    <React.Fragment>
      {/* Title */}
      <DialogContentText
        sx={{ mb: 3 }}
      >{`Select a way to upload your data`}</DialogContentText>

      {/* List of dataloaders */}
      {!loading && (
        <ItemSelector
          itemsList={dataloaders}
          selectedItem={selectedDataloader}
          setSelectedItem={setSelectedDataloader}
        />
      )}
    </React.Fragment>
  );
}

SelectDataloaderStep.propTypes = {
  newDataset: PropTypes.shape({
    task_name: PropTypes.string,
    dataloader: PropTypes.string,
  }).isRequired,
  setNewDataset: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default SelectDataloaderStep;
