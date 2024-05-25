import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";
import { getComponents as getComponentsRequest } from "../../api/component";
import ItemSelectorWithInfo from "../custom/ItemSelectorWithInfo";
import { DialogContentText, Grid } from "@mui/material";

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
      const dataloaders = await getComponentsRequest({
        selectTypes: ["DataLoader"],
      });

      setDataloaders(dataloaders);
      if (newDataset.dataloader !== "") {
        const previouslySelectedDataloader =
          dataloaders.find(
            (dataloader) => dataloader.name === newDataset.dataloader,
          ) || {};
        setSelectedDataloader(previouslySelectedDataloader);
      }
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain compatible dataloaders");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  }

  // updates the modal state with the name of the dataloader that is selected by the user
  useEffect(() => {
    if (selectedDataloader && Object.keys(selectedDataloader).length === 0) {
      setNewDataset({ ...newDataset, dataloader: "" });
    } else if (selectedDataloader && "name" in selectedDataloader) {
      setNewDataset({ ...newDataset, dataloader: selectedDataloader.name });
      setNextEnabled(true);
    }
  }, [selectedDataloader]);

  // fetches the available dataloaders
  useEffect(() => {
    getCompatibleDataloaders();
  }, []);
  return (
    <Grid
      container
      direction="column"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={2}
    >
      {/* Title */}
      <Grid item>
        <DialogContentText
          sx={{ mb: 3 }}
        >{`Select a way to upload your data`}</DialogContentText>
      </Grid>
      {/* List of dataloaders */}
      <Grid item>
        {!loading && (
          <ItemSelectorWithInfo
            itemsList={dataloaders}
            selectedItem={selectedDataloader}
            setSelectedItem={setSelectedDataloader}
          />
        )}
      </Grid>
    </Grid>
  );
}

SelectDataloaderStep.propTypes = {
  newDataset: PropTypes.shape({
    dataloader: PropTypes.string,
  }).isRequired,
  setNewDataset: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default SelectDataloaderStep;
