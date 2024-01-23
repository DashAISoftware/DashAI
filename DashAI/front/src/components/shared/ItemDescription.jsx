import { Box, Stack, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

function ItemDescription({ title, description, images }) {
  return (
    <Stack>
      <Typography variant="h6" sx={{ mb: 4 }}>
        {title}
      </Typography>
      {images &&
        images.map((img, i) => (
          <Box
            component={"img"}
            src={img}
            alt={`Description image ${img}`}
            key={img}
            style={{ borderRadius: "10px", maxWidth: "400px" }}
          />
        ))}
      <Typography>{description}</Typography>
    </Stack>
  );
}

ItemDescription.propTypes = {
  title: PropTypes.string.isRequired,
  images: PropTypes.arrayOf(PropTypes.string),
  description: PropTypes.string,
};

export default ItemDescription;
