import { Box } from "@mui/material";
import { useTheme } from "@mui/material/styles";

export default function CenterBox({ children }) {
  const theme = useTheme();

  return (
    <Box
      width={"100%"}
      height={"100%"}
      sx={{
        border: `0.1px solid ${theme.palette.divider}`,
        borderTop: "none",
        overflow: "auto",
        scrollbarGutter: "stable",
      }}
      p={2}
    >
      {children}
    </Box>
  );
}
