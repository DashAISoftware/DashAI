import React, { useEffect, useState } from "react";
import {
  Grid,
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
 * @param {object[]} itemsList The list of items to select from
 * @param {object} selectedItem The item from the list that has been selected.
 * @param {function} setSelectedItem function to change the value of the selected item
 */
function ItemSelector({ itemsList, selectedItem, setSelectedItem }) {
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
    setSelectedIndex(index);
    setSelectedItem(data);
  };

  // If there was a previously selected item, it highlights it using its index in the list.
  useEffect(() => {
    if (selectedItem !== undefined && Object.keys(selectedItem).length > 0) {
      const previouslySelectedItemIndex = itemsList.findIndex(
        (item) => item.class === selectedItem.class,
      );
      setSelectedIndex(previouslySelectedItemIndex);
    }
  }, []);

  return (
    <Grid item xs={12} md={6}>
      <Paper sx={{ p: 2, pt: 0 }} square>
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
  }),
  setSelectedItem: PropTypes.func.isRequired,
};

ItemSelector.defaultProps = {
  selectedItem: undefined,
};
export default ItemSelector;