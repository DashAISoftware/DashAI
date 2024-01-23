import { Grid, Paper } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import ItemDescription from "./ItemDescription";
import ItemSelectorWithSearch from "./ItemSelectorWithSearch";
function ItemSelectorWithDescriptionContainer({
  itemsList,
  setSelectedItem,
  disabled,
  selectedItemName,
  ...descriptionProps
}) {
  return (
    <Grid container columns={{ xs: 12, md: 15 }}>
      {/* Item list */}
      <Grid item xs={12} md={7}>
        <Paper>
          <ItemSelectorWithSearch
            itemsList={itemsList}
            disabled={disabled}
            selectedItemName={selectedItemName}
            setSelectedItem={setSelectedItem}
          />
        </Paper>
      </Grid>
      <Grid item xs={12} md={1} />
      <Grid item xs={12} md={7}>
        <Paper sx={{ p: 2, height: "100%" }}>
          <ItemDescription {...descriptionProps} />
        </Paper>
      </Grid>
    </Grid>
  );
}

ItemSelectorWithDescriptionContainer.propTypes = {
  itemsList: PropTypes.arrayOf(PropTypes.shape({ class: PropTypes.string }))
    .isRequired,
  setSelectedItem: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  selectedItemName: PropTypes.string,
};

ItemSelectorWithDescriptionContainer.defaultProps = {
  selectedItemKey: null,
  disabled: false,
};

export default ItemSelectorWithDescriptionContainer;
