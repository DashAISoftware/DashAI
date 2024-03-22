import { List, ListItem, ListItemButton, ListItemText } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
/**
 *This component renders a list of items so that the user can select one.
 * @param {object[]} itemsList The list of items to select from
 * @param {object} selectedItem The item from the list that has been selected.
 * @param {function} setSelectedItem function to change the value of the selected item
 * @param {bool} disabled true to disable the item selection, false to enable it
 */
function ItemSelector({
  itemsList,
  selectedItemName,
  setSelectedItem,
  disabled,
}) {
  return (
    <List sx={{ width: "100%" }}>
      {itemsList.map((item) => {
        return (
          <ListItem
            key={`list-button-${item.name}`}
            disablePadding
            sx={{
              pointerEvents: disabled ? "none" : "auto",
              opacity: disabled ? 0.5 : 1,
              overflow: "hidden",
            }}
          >
            <ListItemButton
              selected={selectedItemName === item.name}
              onClick={() => setSelectedItem(item)}
            >
              <ListItemText primary={item.name} />
            </ListItemButton>
          </ListItem>
        );
      })}
    </List>
  );
}

ItemSelector.propTypes = {
  itemsList: PropTypes.arrayOf(PropTypes.shape({ name: PropTypes.string }))
    .isRequired,
  selectedItemName: PropTypes.string,
  setSelectedItem: PropTypes.func,
  disabled: PropTypes.bool,
};

ItemSelector.defaultProps = {
  selectedItem: undefined,
  disabled: false,
};

export default ItemSelector;
