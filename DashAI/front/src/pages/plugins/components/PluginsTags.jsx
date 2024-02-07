import React from "react";
import { Grid, Chip } from "@mui/material";
import PropTypes from "prop-types";

function PluginTags({ tags }) {
  return (
    <Grid container columnGap={1}>
      {tags.map((tag, i) => (
        <Chip key={i} size="small" label={tag} />
      ))}
    </Grid>
  );
}

PluginTags.propTypes = {
  tags: PropTypes.arrayOf(PropTypes.string).isRequired,
};

export default PluginTags;
