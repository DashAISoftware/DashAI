import React, { useRef, useEffect, useState } from "react";
import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";

/**
 * This component is a container for a box with a title
 * @param {string} title title of the box
 * @param {node} children content of the box
 */

function BoxWithTitle({ title, children, boderColor = "grey.700" }) {
  const titleRef = useRef(null);
  const [titleWidth, setTitleWidth] = useState(0);

  useEffect(() => {
    if (titleRef.current) {
      setTitleWidth(titleRef.current.offsetWidth);
    }
  }, [title]);

  return (
    <Box
      border={1}
      borderColor={boderColor}
      borderRadius={2}
      position="relative"
    >
      <Box
        ref={titleRef}
        sx={{
          position: "absolute",
          top: -12,
          left: 8,
          backgroundColor: "inherit",
          px: 1,
          zIndex: 3,
        }}
      >
        <Typography variant="subtitle2">{title}</Typography>
      </Box>

      <Box
        sx={{
          position: "absolute",
          top: -12, // Adjust this value as needed
          left: 8,
          width: titleWidth, // Set the width to the title box width
          backgroundColor: "inherit",
          height: 20, // This should be the same as the border width
          zIndex: 2,
        }}
      />

      {children}
    </Box>
  );
}

BoxWithTitle.propTypes = {
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  boderColor: PropTypes.string,
};

export default BoxWithTitle;
