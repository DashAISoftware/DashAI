import React from "react";
import { Grid, Typography, Paper } from "@mui/material";
import PropTypes from "prop-types";
import ItemSelector from "./ItemSelector";
/**
 *This component renders a list of items so that the user can select one.
  It also renders a description of the item that the user selects along with images (if any).
 * @param {object[]} itemsList The list of items to select from
 * @param {object} selectedItem The item from the list that has been selected.
 * @param {function} setSelectedItem function to change the value of the selected item
 */
function ItemSelectorWithInfo({
  itemsList,
  selectedItem,
  setSelectedItem,
  disabled,
}) {
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
    <Grid
      container
      direction="row"
      justifyContent="space-around"
      alignItems="stretch"
      spacing={3}
    >
      {/* Item list */}
      <Grid item xs={12} md={6}>
        <Paper>
          <ItemSelector
            itemsList={itemsList}
            selectedItem={selectedItem}
            setSelectedItem={setSelectedItem}
            disabled={disabled}
          />
        </Paper>
      </Grid>

      {/* Section that describes the selected item using text and images (if any) */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 2, height: "100%" }}>
          <Grid
            container
            direction="row"
            justifyContent="center"
            alignContent="flex-start"
          >
            {selectedItem && Object.keys(selectedItem).length > 0 ? (
              <>
                <Grid item xs={12}>
                  <Typography variant="h6" sx={{ mb: 4 }}>
                    {selectedItem.name}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  {selectedItem.schema?.images === undefined
                    ? null
                    : displayImages(selectedItem.schema.images)}
                  <Typography>
                    {selectedItem.description !== null
                      ? selectedItem.description
                      : selectedItem.schema?.description}
                  </Typography>
                </Grid>
              </>
            ) : (
              <Grid item xs={12}>
                <Typography variant="subtitle1">
                  Select a task to see the description.
                </Typography>
              </Grid>
            )}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}

ItemSelectorWithInfo.propTypes = {
  itemsList: PropTypes.arrayOf(PropTypes.shape({ class: PropTypes.string }))
    .isRequired,
  selectedItem: PropTypes.shape({
    name: PropTypes.string,
    schema: PropTypes.shape({
      description: PropTypes.string,
      images: PropTypes.arrayOf(PropTypes.string),
    }),
    description: PropTypes.string,
  }),
  setSelectedItem: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
};

ItemSelectorWithInfo.defaultProps = {
  selectedItem: undefined,
  disabled: false,
};
export default ItemSelectorWithInfo;
