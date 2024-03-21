import React from "react";
import { Box, Typography } from "@mui/material";

// eslint-disable-next-line react/prop-types
function BoxWithTitle({ title, children }) {
  return (
    <Box border={1} borderColor="grey.700" borderRadius={2} position="relative">
      <Box
        sx={{
          position: "absolute",
          top: -12,
          left: 8,
          backgroundColor: "inherit",
          px: 1,
          zIndex: 2,
        }}
      >
        <Typography variant="subtitle2">{title}</Typography>
      </Box>

      {children}
    </Box>
  );
}

export default BoxWithTitle;
