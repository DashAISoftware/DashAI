import React from "react";
import { Grid } from "@mui/material";
import PluginCard from "./PluginsCard";
import PropTypes from "prop-types";

function PluginsGrid({ pluginsToShow, cardView }) {
  return (
    <Grid
      container
      spacing={cardView ? 4 : 2}
      direction={cardView ? "row" : "column"}
    >
      {pluginsToShow.map((plugin, i) => (
        <Grid
          key={i}
          item
          xs={cardView ? 4 : 12}
          height={cardView ? "250px" : "auto"}
        >
          <PluginCard plugin={plugin} cardView={cardView} />
        </Grid>
      ))}
    </Grid>
  );
}

PluginsGrid.propTypes = {
  pluginsToShow: PropTypes.arrayOf(
    PropTypes.shape({
      name: PropTypes.string.isRequired,
      description: PropTypes.string.isRequired,
      tags: PropTypes.arrayOf(PropTypes.string).isRequired,
      installed: PropTypes.bool,
      enabled: PropTypes.bool,
    }),
  ),
  cardView: PropTypes.bool,
};

export default PluginsGrid;
