import { TextField } from "@mui/material";
import { styled } from "@mui/material/styles";

export const Input = styled(TextField)(({ theme }) => ({
  width: "100%",
  ".MuiFormHelperText-root": {
    height: 40,
  },
}));
