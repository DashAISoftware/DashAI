import AddIcon from "@mui/icons-material/Add";
import { Box, Button } from "@mui/material";
import { t } from "i18next";

export default function NewItemButton({
  onClick,
  title = t("common:newItem", "New Item"),
  EndIcon = AddIcon,
}) {
  return (
    <Button
      variant="contained"
      sx={{
        bgcolor: "primary.main",
        borderRadius: 1,
        px: 4,
        py: 0,
        display: "flex",
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
        height: "100%",
        width: "100%",
        textTransform: "none",
        "&:hover": { bgcolor: "secondary.main" },
      }}
      onClick={onClick}
      endIcon={<EndIcon />}
    >
      <Box
        component="span"
        sx={{
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
      >
        {title}
      </Box>
    </Button>
  );
}
