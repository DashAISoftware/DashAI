import React, { useState, useEffect } from "react";
import {
  Grid,
  DialogContentText,
  Typography,
  Paper,
  List,
  ListItem,
  TextField,
  ListItemButton,
  ListItemText,
  InputAdornment,
  IconButton,
} from "@mui/material";
import { Clear as ClearIcon } from "@mui/icons-material";
import PropTypes from "prop-types";
import { getTasks as getTasksRequest } from "../../api/task";
import { getCompatibleDataloaders as getCompatibleDataloadersRequest } from "../../api/dataloader";
import { useSnackbar } from "notistack";
import FormTooltip from "../ConfigurableObject/FormTooltip";
/**
 *This component renders a list of items according to their type so that the user can select one of these items.
  It also renders a description of the item that the user selects along with images (if any).
 * @param {{"tasks"|"dataloaders"}} itemsType The type of items to build the list. They are limited to 'tasks' and 'dataloaders' only.
 * @param {string} itemsName The name of the items in the list, it is used to render the text "Select a {itemsName}"
 * @param {object} newDataset An object that stores all the important states for the dataset modal.
 * @param {function} setNewDataset function that modifies newDataset state
 * @param {function} setNextEnabled function to enable or disable the "Next" button in the dataset modal.
 */
function ItemsList({
  itemsType,
  itemsName,
  newDataset,
  setNewDataset,
  setNextEnabled,
}) {
  const [list, setList] = useState([]);
  const [itemsToShow, setItemsToShow] = useState(list.map(() => true));
  const [selectedItem, setSelectItem] = useState();
  const [searchField, setSearchField] = React.useState("");
  const [selectedIndex, setSelectedIndex] = useState(null);
  const { enqueueSnackbar } = useSnackbar();

  // fetches the dataloaders that are compatible with the previously selected task
  async function getCompatibleDataloaders() {
    try {
      const dataloaders = await getCompatibleDataloadersRequest(
        newDataset.task_name,
      );
      setList(dataloaders);
      setItemsToShow(dataloaders.map(() => true));
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
      //
    }
  }

  // fetches all the available tasks
  async function getTasks() {
    try {
      const tasks = await getTasksRequest();
      setList(tasks);
      setItemsToShow(tasks.map(() => true));
    } catch (error) {
      enqueueSnackbar("Error while trying to obtain available tasks", {
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
    }
  }

  // Fetches data depending on what is needed (task/dataloader)
  useEffect(() => {
    switch (itemsType) {
      case "tasks":
        getTasks();
        return;
      case "dataloaders":
        getCompatibleDataloaders();
        return;
      default:
        throw new Error(
          `Error while rendering list: ${itemsType} is not a valid list item type`,
        );
    }
  }, []);

  const handleClearSearchField = (event) => {
    setSearchField("");
    setItemsToShow(list);
  };

  const handleSearchFieldChange = (event) => {
    setSearchField(event.target.value.toLowerCase());
    setItemsToShow(
      list.map((val) => val.name.toLowerCase().includes(event.target.value)),
    );
  };

  const handleListItemClick = (data, index) => {
    setSelectedIndex(index);
    setSelectItem(data);
    switch (itemsType) {
      case "tasks":
        setNewDataset({ ...newDataset, task_name: data.class });
        break;
      case "dataloaders":
        setNewDataset({ ...newDataset, dataloader: data.class });
        break;
      default:
        throw new Error(
          `Error while setting value: ${itemsType} is not a valid list item type`,
        );
    }
    setNextEnabled(true);
  };

  // Display images that help to describe the item selected by the user
  const displayImages = (images) => {
    const imageElements = images.map((img, i) => (
      <img
        src={img}
        alt={`${selectedItem.name} info ${i}`}
        key={img}
        style={{ borderRadius: "10px", maxWidth: "400px" }}
      />
    ));
    return (
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        {imageElements}
      </div>
    );
  };

  return (
    <Paper variant="outlined" sx={{ p: 4 }}>
      <DialogContentText sx={{ mb: 3 }}>
        {`Select a ${itemsName}`}
      </DialogContentText>
      <Grid
        container
        direction="row"
        justifyContent="space-around"
        alignItems="stretch"
        spacing={3}
      >
        {/* Textfield to filter items and the list of items */}
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2, pt: 0 }}>
            <List sx={{ width: "100%" }}>
              <ListItem disablePadding>
                <TextField
                  id={`${itemsName}-search-input`}
                  fullWidth
                  label="Search..."
                  type="search"
                  variant="standard"
                  value={searchField}
                  onChange={handleSearchFieldChange}
                  size="small"
                  sx={{ mb: 2 }}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment
                        position="end"
                        onClick={handleClearSearchField}
                      >
                        <IconButton>
                          <ClearIcon />
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </ListItem>
              {list.map((item, index) => {
                return (
                  <ListItem
                    key={`${itemsName}-list-button-${item.class}`}
                    disablePadding
                    sx={{ display: itemsToShow[index] ? "show" : "none" }}
                  >
                    <ListItemButton
                      selected={selectedIndex === index}
                      onClick={() => handleListItemClick(item, index)}
                    >
                      <ListItemText primary={item.name} />
                      <FormTooltip contentStr={item.help} />
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </List>
          </Paper>
        </Grid>

        {/* Section that describes the selected item using text and images (if any) */}
        <Grid item xs={12} md={6}>
          <Paper variant="outlined" sx={{ p: 2, display: "flex" }}>
            {selectedItem !== undefined ? (
              <div>
                <Typography>{selectedItem.name}</Typography>
                <hr />
                {selectedItem.images === undefined
                  ? null
                  : displayImages(selectedItem.images)}
                <Typography>{selectedItem.description}</Typography>
              </div>
            ) : (
              <Typography>Select an option to know more!</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Paper>
  );
}

ItemsList.propTypes = {
  itemsType: PropTypes.oneOf(["tasks", "dataloaders"]).isRequired,
  itemsName: PropTypes.string.isRequired,
  newDataset: PropTypes.shape({
    task_name: PropTypes.string,
    dataloader_name: PropTypes.string,
  }).isRequired,
  setNewDataset: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default ItemsList;
