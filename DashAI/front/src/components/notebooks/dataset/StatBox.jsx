import React, { useRef, useState } from "react";
import { Paper, Typography, Tooltip } from "@mui/material";
import { useTheme } from "@mui/material/styles";

export const StatBox = ({ label, value }) => {
  const theme = useTheme();
  const textRef = useRef(null);
  const [isTruncated, setIsTruncated] = useState(false);

  const handleMouseEnter = () => {
    if (textRef.current) {
      setIsTruncated(textRef.current.scrollWidth > textRef.current.clientWidth);
    }
  };

  return (
    <Paper
      elevation={1}
      sx={{
        p: 4,
        textAlign: "center",
        borderRadius: 2,
        bgcolor: theme.palette.ui.panelMedium,
        width: "200px",
        overflow: "hidden",
      }}
    >
      <Tooltip title={isTruncated ? String(value) : ""} placement="top">
        <Typography
          ref={textRef}
          variant="h5"
          fontWeight="bold"
          onMouseEnter={handleMouseEnter}
          sx={{
            color: theme.palette.text.primary,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {value}
        </Typography>
      </Tooltip>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Paper>
  );
};
