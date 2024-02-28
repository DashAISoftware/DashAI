import React from "react";
import { Grid, Chip } from "@mui/material";
import PropTypes from "prop-types";

/**
 * component for plugin tags chips
 * @param {} tags tags to display
 * @returns
 */
function PluginTags({ tags }) {
  return (
    <Grid container columnGap={1}>
      {tags.map((tag, i) => (
        <Chip key={i} size="small" label={tag.name} />
      ))}
    </Grid>
  );
}

PluginTags.propTypes = {
  tags: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.number.isRequired,
      name: PropTypes.string.isRequired,
      plugin_id: PropTypes.number.isRequired,
    }),
  ).isRequired,
};

export default PluginTags;
