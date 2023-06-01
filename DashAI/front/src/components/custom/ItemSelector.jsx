import React, { useEffect, useState } from "react";
import {
  Grid,
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
import FormTooltip from "../ConfigurableObject/FormTooltip";
/**
 *This component renders a list of items so that the user can select one.
  It also renders a description of the item that the user selects along with images (if any).
 * @param {object[]} itemsList The list of items to select from
 * @param {object} selectedItem The item from the list that has been selected.
 * @param {function} setSelectedItem function to change the value of the selected item
 * @param {bool} disabled true to disable the item selection, false to enable it
 */
function ItemSelector({ itemsList, selectedItem, setSelectedItem, disabled }) {
  const [itemsToShow, setItemsToShow] = useState(itemsList.map(() => true));
  const [searchField, setSearchField] = React.useState("");
  const [selectedIndex, setSelectedIndex] = useState(null);

  const handleClearSearchField = (event) => {
    setSearchField("");
    setItemsToShow(itemsList);
  };

  const handleSearchFieldChange = (event) => {
    setSearchField(event.target.value.toLowerCase());
    setItemsToShow(
      itemsList.map((val) =>
        val.name.toLowerCase().includes(event.target.value),
      ),
    );
  };

  const handleListItemClick = (data, index) => {
    if (!disabled) {
      setSelectedIndex(index);
      setSelectedItem(data);
    }
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

  // If there was a previously selected item, it highlights it using its index in the list.
  useEffect(() => {
    if (Object.keys(selectedItem).length > 0) {
      const previouslySelectedItemIndex = itemsList.findIndex(
        (item) => item.class === selectedItem.class,
      );
      setSelectedIndex(previouslySelectedItemIndex);
    }
  }, []);

  return (
    <Paper variant="outlined" sx={{ p: 4 }}>
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
                  id="item-search-input"
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
              {itemsList.map((item, index) => {
                return (
                  <ListItem
                    key={`list-button-${item.class}`}
                    disablePadding
                    sx={{
                      display: itemsToShow[index] ? "show" : "none",
                      pointerEvents: disabled ? "none" : "auto",
                      opacity: disabled ? 0.5 : 1,
                    }}
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

ItemSelector.propTypes = {
  itemsList: PropTypes.arrayOf(PropTypes.shape({ class: PropTypes.string }))
    .isRequired,
  selectedItem: PropTypes.shape({
    name: PropTypes.string,
    class: PropTypes.string,
    description: PropTypes.string,
    images: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
  setSelectedItem: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
};

ItemSelector.defaultProps = {
  disabled: false,
};
export default ItemSelector;
